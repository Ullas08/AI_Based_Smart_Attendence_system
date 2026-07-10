"""
Attendance routes: view, search, and manage attendance records.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from routes.auth import login_required
from utils.db import get_attendance, get_departments, get_attendance_stats
from datetime import datetime

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')


@attendance_bp.route('/')
@login_required
def index():
    date_filter = request.args.get('date', '')
    student_filter = request.args.get('student', '')
    dept_filter = request.args.get('dept', '')

    records = get_attendance(
        date_filter=date_filter or None,
        student_filter=student_filter or None,
        dept_filter=dept_filter or None
    )
    departments = get_departments()
    today = datetime.now().strftime('%Y-%m-%d')

    return render_template('attendance.html',
                           records=records,
                           departments=departments,
                           date_filter=date_filter,
                           student_filter=student_filter,
                           dept_filter=dept_filter,
                           today=today,
                           total=len(records))


@attendance_bp.route('/api/list')
@login_required
def api_list():
    """JSON endpoint for attendance data."""
    date_filter = request.args.get('date', None)
    student_filter = request.args.get('student', None)
    dept_filter = request.args.get('dept', None)
    records = get_attendance(date_filter, student_filter, dept_filter)
    return jsonify({'records': records, 'total': len(records)})
