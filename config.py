"""
Configuration module for AI Smart Attendance System.
Loads settings from .env file with sensible defaults.
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production-abc123xyz789')
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database
    DATABASE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'attendance.db')
    
    # Admin defaults
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'Admin@123')
    
    # AI / Face Recognition
    CONFIDENCE_THRESHOLD = float(os.getenv('CONFIDENCE_THRESHOLD', 0.75))
    MIN_FACE_IMAGES = int(os.getenv('MIN_FACE_IMAGES', 30))
    MAX_FACE_IMAGES = int(os.getenv('MAX_FACE_IMAGES', 100))
    IMAGE_SIZE = int(os.getenv('IMAGE_SIZE', 128))
    
    # Camera
    CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
    
    # Paths (relative to project root)
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATASET_PATH = os.path.join(BASE_DIR, os.getenv('DATASET_PATH', 'dataset'))
    MODELS_PATH = os.path.join(BASE_DIR, os.getenv('MODELS_PATH', 'trained_models'))
    UPLOADS_PATH = os.path.join(BASE_DIR, os.getenv('UPLOADS_PATH', 'uploads'))
    
    # Session
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    
    @classmethod
    def init_dirs(cls):
        """Create required directories if they don't exist."""
        for path in [cls.DATASET_PATH, cls.MODELS_PATH, cls.UPLOADS_PATH]:
            os.makedirs(path, exist_ok=True)
