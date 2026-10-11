import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

from config import Config
from database import get_student_by_id
from attendance import get_student_attendance_summary, get_student_course_attendance, get_student_daily_attendance


def generate_student_pdf_report(student_id):
    """
    Generates a PDF attendance report for a given student ID.
    Returns: file path to generated PDF file.
    """
    student = get_student_by_id(student_id)
    if not student:
        return None

    summary = get_student_attendance_summary(student_id)
    courses = get_student_course_attendance(student_id)
    daily = get_student_daily_attendance(student_id)

    filename = f"report_{student_id}.pdf"
    filepath = os.path.join(Config.REPORTS_DIR, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#2563eb'),
        alignment=1, # Center
        spaceAfter=12
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        alignment=1,
        spaceAfter=20
    )
    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1e293b'),
        spaceBefore=14,
        spaceAfter=8
    )

    # Title & Subtitle
    story.append(Paragraph("FACIAL ATTENDANCE MANAGEMENT SYSTEM", title_style))
    story.append(Paragraph(f"Official Attendance Report for Student: {student['name']} ({student_id})", subtitle_style))
    story.append(Spacer(1, 10))

    # Student Info Table
    info_data = [
        ["Student Name:", student['name'], "Student ID:", student['student_id']],
        ["Department:", student['department'], "Year / Section:", f"Year {student['year']} - Sec {student['section']}"],
        ["Email:", student['email'], "Phone:", student.get('phone', 'N/A')]
    ]
    info_table = Table(info_data, colWidths=[100, 170, 90, 170])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#334155')),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 15))

    # Summary Metrics Card Table
    story.append(Paragraph("1. Consolidated Attendance Summary", h2_style))
    summary_data = [
        ["Total Completed Classes", "Present Count", "Absent Count", "Overall Attendance %"],
        [str(summary['total_classes']), str(summary['present']), str(summary['absent']), f"{summary['percentage']}%"]
    ]
    summary_table = Table(summary_data, colWidths=[130, 130, 130, 140])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2563eb')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f1f5f9')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    # Course-wise Table
    story.append(Paragraph("2. Course-Wise Breakdown", h2_style))
    course_headers = ["Subject Name", "Total Classes", "Present", "Absent", "Attendance %"]
    course_rows = [course_headers]
    for c in courses:
        course_rows.append([c['subject'], str(c['total_classes']), str(c['present']), str(c['absent']), f"{c['percentage']}%"])

    if len(course_rows) == 1:
        course_rows.append(["No recorded course data", "-", "-", "-", "-"])

    course_table = Table(course_rows, colWidths=[180, 85, 85, 85, 95])
    course_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e293b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (0, 0), (0, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
    ]))
    story.append(course_table)

    # Build PDF
    doc.build(story)
    return filepath
