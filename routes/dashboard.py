"""Dashboard routes."""

from flask import Blueprint, render_template, jsonify
from routes.auth import login_required
from utils.db import get_attendance_stats, get_all_students, get_attendance

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    stats = get_attendance_stats()
    return render_template('dashboard.html', stats=stats)


@dashboard_bp.route('/api/stats')
@login_required
def api_stats():
    """JSON endpoint for live dashboard stats refresh."""
    stats = get_attendance_stats()
    return jsonify(stats)
