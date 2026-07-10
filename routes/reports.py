"""
Report export routes.
Supports downloading attendance data as Excel, CSV, or PDF.
"""

from flask import Blueprint, render_template, request, send_file, flash, redirect, url_for
from routes.auth import login_required
from utils.db import get_attendance, get_departments
from utils.export_utils import export_to_excel, export_to_csv, export_to_pdf
from datetime import datetime
import io

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/')
@login_required
def index():
    departments = get_departments()
    today = datetime.now().strftime('%Y-%m-%d')
    return render_template('reports.html', departments=departments, today=today)


@reports_bp.route('/export')
@login_required
def export():
    fmt = request.args.get('format', 'excel')
    date_filter = request.args.get('date', None) or None
    student_filter = request.args.get('student', None) or None
    dept_filter = request.args.get('dept', None) or None

    records = get_attendance(date_filter, student_filter, dept_filter)

    title = 'Attendance Report'
    if date_filter:
        title += f' — {date_filter}'

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    if fmt == 'csv':
        csv_data = export_to_csv(records)
        return send_file(
            io.BytesIO(csv_data.encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'attendance_{timestamp}.csv'
        )
    elif fmt == 'pdf':
        pdf_data = export_to_pdf(records, title=title)
        return send_file(
            pdf_data,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'attendance_{timestamp}.pdf'
        )
    else:  # default: Excel
        excel_data = export_to_excel(records, title=title)
        return send_file(
            excel_data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'attendance_{timestamp}.xlsx'
        )
