"""
Student management routes.
Handles add/edit/delete students and face dataset capture via AJAX.
"""

import os
import base64
import cv2
import numpy as np
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from routes.auth import login_required
from utils.db import (
    get_all_students, get_student_by_pk, get_student_by_id,
    add_student, update_student, delete_student,
    mark_student_trained, get_trained_students
)
from utils.face_capture import (
    capture_faces_from_frame, count_captured_images, get_student_dataset_path
)
from config import Config
import re
import shutil

students_bp = Blueprint('students', __name__, url_prefix='/students')

DEPARTMENTS = ['Computer Science', 'Electronics', 'Mechanical', 'Civil', 'Electrical',
               'Information Technology', 'Biotechnology', 'Chemical', 'Other']
SEMESTERS = [str(i) for i in range(1, 9)]


def sanitize_input(value, max_len=200):
    """Strip and limit input length."""
    return str(value).strip()[:max_len] if value else ''


def validate_email(email):
    return re.match(r'^[^@]+@[^@]+\.[^@]+$', email) is not None if email else True


def validate_phone(phone):
    return re.match(r'^\+?[\d\s\-]{7,15}$', phone) is not None if phone else True


@students_bp.route('/')
@login_required
def index():
    search = sanitize_input(request.args.get('search', ''))
    dept = sanitize_input(request.args.get('dept', ''))
    students = get_all_students()
    if search:
        s = search.lower()
        students = [st for st in students if s in st['name'].lower() or s in st['student_id'].lower()]
    if dept:
        students = [st for st in students if st['department'] == dept]
    return render_template('students.html', students=students, search=search,
                           departments=DEPARTMENTS, dept_filter=dept)


@students_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    errors = {}
    form_data = {}

    if request.method == 'POST':
        form_data = {
            'student_id': sanitize_input(request.form.get('student_id')),
            'name': sanitize_input(request.form.get('name')),
            'department': sanitize_input(request.form.get('department')),
            'semester': sanitize_input(request.form.get('semester')),
            'email': sanitize_input(request.form.get('email')),
            'phone': sanitize_input(request.form.get('phone')),
        }

        # Validation
        if not form_data['student_id']:
            errors['student_id'] = 'Student ID is required'
        elif not re.match(r'^[A-Za-z0-9\-_]{3,20}$', form_data['student_id']):
            errors['student_id'] = 'ID must be 3-20 alphanumeric characters'

        if not form_data['name']:
            errors['name'] = 'Name is required'
        elif len(form_data['name']) < 2:
            errors['name'] = 'Name too short'

        if form_data['department'] not in DEPARTMENTS:
            errors['department'] = 'Invalid department'

        if form_data['semester'] not in SEMESTERS:
            errors['semester'] = 'Invalid semester'

        if form_data['email'] and not validate_email(form_data['email']):
            errors['email'] = 'Invalid email format'

        if form_data['phone'] and not validate_phone(form_data['phone']):
            errors['phone'] = 'Invalid phone number'

        if not errors:
            success, msg = add_student(**form_data)
            if success:
                flash(f'Student {form_data["name"]} added! Now capture face images.', 'success')
                return redirect(url_for('students.capture_face',
                                        student_id=form_data['student_id']))
            else:
                errors['student_id'] = msg

    return render_template('student_add.html', errors=errors, form_data=form_data,
                           departments=DEPARTMENTS, semesters=SEMESTERS)


@students_bp.route('/edit/<int:pk>', methods=['GET', 'POST'])
@login_required
def edit(pk):
    student = get_student_by_pk(pk)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))

    errors = {}
    if request.method == 'POST':
        name = sanitize_input(request.form.get('name'))
        department = sanitize_input(request.form.get('department'))
        semester = sanitize_input(request.form.get('semester'))
        email = sanitize_input(request.form.get('email'))
        phone = sanitize_input(request.form.get('phone'))

        if not name:
            errors['name'] = 'Name is required'
        if department not in DEPARTMENTS:
            errors['department'] = 'Invalid department'
        if email and not validate_email(email):
            errors['email'] = 'Invalid email'
        if phone and not validate_phone(phone):
            errors['phone'] = 'Invalid phone'

        if not errors:
            update_student(pk, name, department, semester, email, phone)
            flash('Student updated successfully!', 'success')
            return redirect(url_for('students.index'))

        student.update({'name': name, 'department': department,
                        'semester': semester, 'email': email, 'phone': phone})

    return render_template('student_edit.html', student=student, errors=errors,
                           departments=DEPARTMENTS, semesters=SEMESTERS)


@students_bp.route('/delete/<int:pk>', methods=['POST'])
@login_required
def delete(pk):
    student = get_student_by_pk(pk)
    if student:
        # Remove dataset folder
        dataset_path = os.path.join(Config.DATASET_PATH, student['student_id'])
        if os.path.exists(dataset_path):
            shutil.rmtree(dataset_path)
        delete_student(pk)
        flash(f'Student {student["name"]} deleted.', 'info')
    return redirect(url_for('students.index'))


@students_bp.route('/capture/<student_id>')
@login_required
def capture_face(student_id):
    student = get_student_by_id(student_id)
    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('students.index'))
    captured = count_captured_images(student_id)
    return render_template('capture.html', student=student, captured=captured,
                           max_images=Config.MAX_FACE_IMAGES,
                           min_images=Config.MIN_FACE_IMAGES)


@students_bp.route('/api/capture-frame', methods=['POST'])
@login_required
def api_capture_frame():
    """Receive a base64 webcam frame, detect and save face."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'success': False, 'error': 'No data'}), 400

    student_id = sanitize_input(data.get('student_id', ''))
    img_b64 = data.get('image', '')

    if not student_id or not img_b64:
        return jsonify({'success': False, 'error': 'Missing fields'}), 400

    student = get_student_by_id(student_id)
    if not student:
        return jsonify({'success': False, 'error': 'Student not found'}), 404

    try:
        # Decode base64 image
        if ',' in img_b64:
            img_b64 = img_b64.split(',')[1]
        img_bytes = base64.b64decode(img_b64)
        np_arr = np.frombuffer(img_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if frame is None:
            return jsonify({'success': False, 'error': 'Invalid image'}), 400

        current_count = count_captured_images(student_id)
        if current_count >= Config.MAX_FACE_IMAGES:
            return jsonify({'success': False, 'error': 'Maximum images reached',
                            'count': current_count})

        saved, face_count = capture_faces_from_frame(frame, student_id, current_count)
        new_count = count_captured_images(student_id)

        return jsonify({
            'success': True,
            'saved': saved,
            'face_count': face_count,
            'count': new_count,
            'complete': new_count >= Config.MIN_FACE_IMAGES
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@students_bp.route('/api/image-count/<student_id>')
@login_required
def api_image_count(student_id):
    count = count_captured_images(student_id)
    return jsonify({'count': count, 'min': Config.MIN_FACE_IMAGES,
                    'max': Config.MAX_FACE_IMAGES})
