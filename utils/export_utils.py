"""
Export utilities for attendance reports.
Supports Excel (xlsx), CSV, and PDF formats.
"""

import io
import csv
from datetime import datetime

import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def records_to_dataframe(records):
    """Convert list of dicts to a cleaned pandas DataFrame."""
    if not records:
        return pd.DataFrame(columns=['ID', 'Student ID', 'Name', 'Department', 'Date', 'Time', 'Confidence', 'Status'])
    df = pd.DataFrame(records)
    rename_map = {
        'id': 'ID',
        'student_id': 'Student ID',
        'student_name': 'Name',
        'department': 'Department',
        'date': 'Date',
        'time': 'Time',
        'confidence': 'Confidence',
        'status': 'Status'
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    if 'Confidence' in df.columns:
        df['Confidence'] = df['Confidence'].apply(lambda x: f"{float(x)*100:.1f}%" if x else '-')
    return df


def export_to_excel(records, title='Attendance Report'):
    """Return Excel bytes for the given attendance records."""
    df = records_to_dataframe(records)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Attendance')
        ws = writer.sheets['Attendance']
        # Auto-width columns
        for col in ws.columns:
            max_len = max((len(str(cell.value)) for cell in col if cell.value), default=10)
            ws.column_dimensions[col[0].column_letter].width = max_len + 4
    output.seek(0)
    return output


def export_to_csv(records):
    """Return CSV string for the given attendance records."""
    df = records_to_dataframe(records)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)
    return output.getvalue()


def export_to_pdf(records, title='Attendance Report'):
    """Return PDF bytes for the given attendance records."""
    output = io.BytesIO()
    doc = SimpleDocTemplate(
        output,
        pagesize=landscape(A4),
        rightMargin=1*cm, leftMargin=1*cm,
        topMargin=1.5*cm, bottomMargin=1*cm
    )
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        'Title', parent=styles['Title'],
        fontSize=16, spaceAfter=12, alignment=TA_CENTER,
        textColor=colors.HexColor('#1a1a2e')
    )
    elements.append(Paragraph(title, title_style))

    sub = ParagraphStyle('Sub', parent=styles['Normal'],
                          fontSize=9, spaceAfter=16, alignment=TA_CENTER,
                          textColor=colors.grey)
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total Records: {len(records)}",
        sub
    ))

    if not records:
        elements.append(Paragraph("No attendance records found.", styles['Normal']))
    else:
        df = records_to_dataframe(records)
        cols = [c for c in df.columns if c != 'ID']
        data = [cols] + df[cols].values.tolist()

        col_widths = [2*cm, 4*cm, 3*cm, 3*cm, 2.5*cm, 2.5*cm, 2.5*cm]
        table = Table(data, colWidths=col_widths, repeatRows=1)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f4ff')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWHEIGHT', (0, 0), (-1, -1), 20),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)

    doc.build(elements)
    output.seek(0)
    return output
