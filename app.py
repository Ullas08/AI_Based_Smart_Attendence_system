"""
AI-Based Smart Attendance System
Main Flask Application Entry Point
"""

import os
from flask import Flask, session
from config import Config
from utils.db import init_db
from utils.face_recognition_engine import load_model

# ─── Blueprint imports ───────────────────────────────────────────────────────
from routes.auth import auth_bp
from routes.dashboard import dashboard_bp
from routes.students import students_bp
from routes.attendance import attendance_bp
from routes.recognition import recognition_bp
from routes.reports import reports_bp


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    # ── Configuration ─────────────────────────────────────────────────────────
    app.secret_key = Config.SECRET_KEY
    app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH
    app.config['PERMANENT_SESSION_LIFETIME'] = Config.PERMANENT_SESSION_LIFETIME

    # ── Initialize directories ────────────────────────────────────────────────
    Config.init_dirs()

    # ── Initialize database ───────────────────────────────────────────────────
    init_db()

    # ── Load AI model if available ────────────────────────────────────────────
    model_loaded = load_model()
    if model_loaded:
        print("[App] Face recognition model loaded ✓")
    else:
        print("[App] No trained model found — train after adding students.")

    # ── Register blueprints ───────────────────────────────────────────────────
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(recognition_bp)
    app.register_blueprint(reports_bp)

    # ── Context processors ────────────────────────────────────────────────────
    @app.context_processor
    def inject_user():
        return {
            'current_user': session.get('admin_username', None),
            'user_role': session.get('admin_role', None),
        }

    # ── Error handlers ────────────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template('500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("  AI-Based Smart Attendance System")
    print("  URL: http://127.0.0.1:5000")
    print(f"  Default Login: admin / Admin@123")
    print("=" * 60)
    app.run(debug=Config.DEBUG, host='0.0.0.0', port=5000, threaded=True)
