"""
Face Recognition Engine.
Loads the trained CNN model and performs real-time face recognition.
"""

import os
import cv2
import numpy as np
from config import Config

CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

_model = None
_label_map = None  # {index: student_id}


def load_model():
    """Load the trained CNN model and label map if available."""
    global _model, _label_map
    model_path = os.path.join(Config.MODELS_PATH, 'face_model.h5')
    label_path = os.path.join(Config.MODELS_PATH, 'label_map.npy')

    if not os.path.exists(model_path) or not os.path.exists(label_path):
        _model = None
        _label_map = None
        return False

    try:
        import tensorflow as tf
        _model = tf.keras.models.load_model(model_path)
        _label_map = np.load(label_path, allow_pickle=True).item()
        return True
    except Exception as e:
        print(f"[RecognitionEngine] Failed to load model: {e}")
        _model = None
        _label_map = None
        return False


def is_model_loaded():
    return _model is not None


def preprocess_face(face_img):
    """Resize and normalize face image for CNN input."""
    resized = cv2.resize(face_img, (Config.IMAGE_SIZE, Config.IMAGE_SIZE))
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    normalized = rgb.astype(np.float32) / 255.0
    return np.expand_dims(normalized, axis=0)


def recognize_faces_in_frame(frame):
    """
    Detect and recognize all faces in a frame.
    Returns list of dicts: {student_id, name, confidence, bbox}
    """
    if _model is None or _label_map is None:
        return []

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
    results = []

    for (x, y, w, h) in faces:
        pad = 15
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame.shape[1], x + w + pad)
        y2 = min(frame.shape[0], y + h + pad)
        face_crop = frame[y1:y2, x1:x2]

        try:
            inp = preprocess_face(face_crop)
            preds = _model.predict(inp, verbose=0)[0]
            idx = int(np.argmax(preds))
            confidence = float(preds[idx])

            if confidence >= Config.CONFIDENCE_THRESHOLD:
                student_id = _label_map.get(idx, 'unknown')
                results.append({
                    'student_id': student_id,
                    'confidence': confidence,
                    'bbox': (x, y, w, h),
                    'unknown': False
                })
            else:
                results.append({
                    'student_id': 'unknown',
                    'confidence': confidence,
                    'bbox': (x, y, w, h),
                    'unknown': True
                })
        except Exception as e:
            print(f"[RecognitionEngine] Prediction error: {e}")

    return results


def annotate_frame(frame, recognition_results, student_lookup):
    """Draw bounding boxes and labels on frame."""
    annotated = frame.copy()
    for r in recognition_results:
        x, y, w, h = r['bbox']
        if r['unknown']:
            color = (0, 0, 255)
            label = f"Unknown ({r['confidence']:.0%})"
        else:
            color = (0, 255, 0)
            name = student_lookup.get(r['student_id'], {}).get('name', r['student_id'])
            label = f"{name} ({r['confidence']:.0%})"

        cv2.rectangle(annotated, (x, y), (x+w, y+h), color, 2)
        # Background for text
        (tw, th), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.65, 2)
        cv2.rectangle(annotated, (x, y - th - 12), (x + tw + 4, y), color, -1)
        cv2.putText(annotated, label, (x + 2, y - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
    return annotated
