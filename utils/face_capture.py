"""
Face capture utility.
Uses OpenCV Haar Cascade to detect and crop faces from webcam,
saving images to the student's dataset folder.
"""

import os
import cv2
import numpy as np
from config import Config

# Load Haar Cascade for face detection
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)


def get_student_dataset_path(student_id):
    """Return the dataset directory for a student."""
    path = os.path.join(Config.DATASET_PATH, student_id)
    os.makedirs(path, exist_ok=True)
    return path


def capture_faces_from_frame(frame, student_id, img_index):
    """
    Detect faces in the given frame and save cropped face.
    Returns (saved, face_count) tuple.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(60, 60)
    )

    saved = 0
    for (x, y, w, h) in faces[:1]:  # Only first face per frame for registration
        # Crop with padding
        pad = 20
        x1 = max(0, x - pad)
        y1 = max(0, y - pad)
        x2 = min(frame.shape[1], x + w + pad)
        y2 = min(frame.shape[0], y + h + pad)

        face_crop = frame[y1:y2, x1:x2]
        face_resized = cv2.resize(face_crop, (Config.IMAGE_SIZE, Config.IMAGE_SIZE))

        path = get_student_dataset_path(student_id)
        filename = os.path.join(path, f"{img_index:04d}.jpg")
        cv2.imwrite(filename, face_resized)
        saved += 1
    return saved, len(faces)


def count_captured_images(student_id):
    """Return number of already-captured face images for a student."""
    path = get_student_dataset_path(student_id)
    return len([f for f in os.listdir(path) if f.endswith('.jpg')])


def draw_detection_overlay(frame, confidence=None, name=None):
    """Draw face detection boxes and labels on frame."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))
    annotated = frame.copy()
    for (x, y, w, h) in faces:
        cv2.rectangle(annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
        if name and confidence:
            label = f"{name} ({confidence:.0%})"
            cv2.putText(annotated, label, (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    return annotated, len(faces)
