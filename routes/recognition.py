"""
Real-time face recognition routes.
Serves the MJPEG video stream with live recognition overlays
and handles attendance marking via AJAX.
"""

import cv2
import json
import threading
import time
from flask import Blueprint, render_template, Response, jsonify, request
from routes.auth import login_required
from utils.face_recognition_engine import (
    load_model, recognize_faces_in_frame, annotate_frame, is_model_loaded
)
from utils.db import mark_attendance, get_student_by_id, get_all_students
from config import Config

recognition_bp = Blueprint('recognition', __name__, url_prefix='/recognition')

# Thread-safe state
_lock = threading.Lock()
_camera = None
_camera_active = False
_last_results = []
_marked_today = set()  # Track recently marked (student_id) to avoid rapid re-marking

# Training state shared across threads
_training_state = {
    'running': False,
    'success': None,      # True/False/None
    'message': '',
    'accuracy': None,
    'error': None,
}


def get_camera():
    global _camera
    if _camera is None or not _camera.isOpened():
        _camera = cv2.VideoCapture(Config.CAMERA_INDEX)
        _camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        _camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return _camera


def release_camera():
    global _camera, _camera_active
    if _camera is not None and _camera.isOpened():
        _camera.release()
    _camera = None
    _camera_active = False


def gen_frames():
    """Generator that yields MJPEG frames with recognition overlays."""
    global _last_results, _camera_active
    _camera_active = True
    
    # Build student lookup dict
    all_students = get_all_students()
    student_lookup = {s['student_id']: s for s in all_students}

    cam = get_camera()
    frame_count = 0

    while _camera_active:
        success, frame = cam.read()
        if not success:
            time.sleep(0.05)
            continue

        frame_count += 1

        # Run recognition every 5 frames for performance
        if frame_count % 5 == 0 and is_model_loaded():
            results = recognize_faces_in_frame(frame)
            with _lock:
                _last_results = results

            # Auto-mark attendance for recognized students
            for r in results:
                if not r['unknown']:
                    sid = r['student_id']
                    if sid not in _marked_today:
                        student = student_lookup.get(sid)
                        if student:
                            success_mark, msg = mark_attendance(
                                sid,
                                student['name'],
                                student['department'],
                                r['confidence']
                            )
                            if success_mark:
                                _marked_today.add(sid)
                                print(f"[Recognition] {msg}")
        else:
            with _lock:
                results = _last_results

        # Annotate frame
        if is_model_loaded():
            student_lookup_local = {s['student_id']: s for s in all_students}
            annotated = annotate_frame(frame, results, student_lookup_local)
        else:
            annotated = frame.copy()
            cv2.putText(annotated, "Model not loaded - Please train first",
                        (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        # FPS overlay
        cv2.putText(annotated, f"AI Smart Attendance", (10, annotated.shape[0] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        ret, buffer = cv2.imencode('.jpg', annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ret:
            continue
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@recognition_bp.route('/')
@login_required
def index():
    model_loaded = is_model_loaded()
    return render_template('recognition.html', model_loaded=model_loaded)


@recognition_bp.route('/video_feed')
@login_required
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


@recognition_bp.route('/stop', methods=['POST'])
@login_required
def stop_camera():
    release_camera()
    return jsonify({'success': True, 'message': 'Camera stopped'})


@recognition_bp.route('/start', methods=['POST'])
@login_required
def start_camera():
    global _camera_active
    load_model()
    _camera_active = True
    return jsonify({'success': True, 'model_loaded': is_model_loaded()})


@recognition_bp.route('/api/status')
@login_required
def api_status():
    with _lock:
        results = _last_results.copy()
    return jsonify({
        'model_loaded': is_model_loaded(),
        'camera_active': _camera_active,
        'detections': len(results),
        'results': [
            {
                'student_id': r['student_id'],
                'confidence': round(r['confidence'] * 100, 1),
                'unknown': r['unknown']
            }
            for r in results
        ]
    })


@recognition_bp.route('/train', methods=['POST'])
@login_required
def train():
    """Trigger model training in a background thread."""
    global _training_state

    if _training_state['running']:
        return jsonify({'success': False, 'message': 'Training already in progress. Please wait.'})

    def run_training():
        global _training_state
        with _lock:
            _training_state = {'running': True, 'success': None, 'message': 'Training in progress...', 'accuracy': None, 'error': None}
        try:
            import sys
            sys.path.insert(0, '.')
            from models.train_model import train_model
            result = train_model()
            print(f"[Training] Result: {result}")
            if result['success']:
                load_model()
                with _lock:
                    _training_state = {
                        'running': False,
                        'success': True,
                        'message': result['message'],
                        'accuracy': result.get('best_accuracy'),
                        'error': None,
                    }
            else:
                with _lock:
                    _training_state = {
                        'running': False,
                        'success': False,
                        'message': result['message'],
                        'accuracy': None,
                        'error': result['message'],
                    }
        except Exception as e:
            import traceback
            err = traceback.format_exc()
            print(f"[Training] EXCEPTION: {err}")
            with _lock:
                _training_state = {
                    'running': False,
                    'success': False,
                    'message': f'Training failed: {str(e)}',
                    'accuracy': None,
                    'error': str(e),
                }

    t = threading.Thread(target=run_training, daemon=True)
    t.start()
    return jsonify({'success': True, 'message': 'Training started in background. This may take a few minutes.'})


@recognition_bp.route('/train/status')
@login_required
def train_status():
    """Return detailed training status including progress and errors."""
    import os
    model_path = os.path.join(Config.MODELS_PATH, 'face_model.h5')
    label_path = os.path.join(Config.MODELS_PATH, 'label_map.npy')
    model_exists = os.path.exists(model_path) and os.path.exists(label_path)

    history = {}
    history_path = os.path.join(Config.MODELS_PATH, 'training_history.json')
    if os.path.exists(history_path):
        with open(history_path) as f:
            history = json.load(f)

    with _lock:
        state = dict(_training_state)

    # Check dataset status for informative messages
    dataset_students = 0
    dataset_ready = 0
    if os.path.exists(Config.DATASET_PATH):
        for d in os.listdir(Config.DATASET_PATH):
            dpath = os.path.join(Config.DATASET_PATH, d)
            if os.path.isdir(dpath):
                dataset_students += 1
                imgs = len([f for f in os.listdir(dpath) if f.lower().endswith('.jpg')])
                if imgs >= Config.MIN_FACE_IMAGES:
                    dataset_ready += 1

    return jsonify({
        'model_exists': model_exists,
        'model_loaded': is_model_loaded(),
        'best_accuracy': round(max(history.get('val_accuracy', [0])) * 100, 2) if history else None,
        'training_running': state['running'],
        'training_success': state['success'],
        'training_message': state['message'],
        'training_error': state['error'],
        'training_accuracy': state['accuracy'],
        'dataset_students': dataset_students,
        'dataset_ready': dataset_ready,
        'min_images': Config.MIN_FACE_IMAGES,
    })
