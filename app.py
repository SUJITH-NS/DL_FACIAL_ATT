from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import os

from config import Config
from database import (
    get_student_by_id, get_staff_by_id, get_students_by_class,
    get_staff_allocations, get_student_notifications, mark_notification_read
)
from auth import (
    authenticate_user, register_student_account, register_staff_account,
    login_required, student_required, staff_required
)
from utils import (
    format_json_response, decode_base64_image, get_today_day_name, get_current_timetable_hour
)
from face_registration import register_student_face_samples
from recognition import recognize_face
from attendance import (
    start_attendance_session, stop_attendance_session, get_active_session,
    get_active_sessions_for_class, get_session_attendance_list, mark_attendance,
    get_student_timetable_status, get_student_attendance_summary,
    get_student_course_attendance, get_student_daily_attendance,
    get_student_weekly_attendance
)
from pdf_generator import generate_student_pdf_report

app = Flask(__name__)
app.config.from_object(Config)

# --- GLOBAL CONTEXT PROCESSOR FOR TEMPLATES ---
@app.context_processor
def inject_global_vars():
    user_name = session.get('user_name', '')
    role = session.get('role', '')
    user_id = session.get('user_id', '')
    return dict(
        current_user_name=user_name,
        current_role=role,
        current_user_id=user_id,
        current_hour=get_current_timetable_hour(),
        today_day=get_today_day_name()
    )

# --- AUTHENTICATION & PAGE ROUTES ---

@app.route('/')
def index():
    if 'user_id' in session and 'role' in session:
        if session['role'] == 'STUDENT':
            return redirect(url_for('student_dashboard'))
        elif session['role'] == 'STAFF':
            return redirect(url_for('staff_dashboard'))
    return redirect(url_for('login_page'))

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        user_id_or_email = request.form.get('user_id_or_email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', '').strip().upper()

        if not user_id_or_email or not password or not role:
            flash("Please fill in all login credentials.", "warning")
            return render_template('login.html')

        success, msg = authenticate_user(user_id_or_email, password, role)
        if success:
            flash(msg, "success")
            if role == 'STUDENT':
                return redirect(url_for('student_dashboard'))
            else:
                return redirect(url_for('staff_dashboard'))
        else:
            flash(msg, "danger")

    return render_template('login.html')

@app.route('/student/signup', methods=['GET', 'POST'])
def student_signup_page():
    if request.method == 'POST':
        student_id = request.form.get('student_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        department = request.form.get('department', '').strip()
        year = request.form.get('year', 4, type=int)
        section = request.form.get('section', '').strip()
        phone = request.form.get('phone', '').strip()

        success, msg = register_student_account(student_id, name, email, password, department, year, section, phone)
        if success:
            flash(msg, "success")
            return redirect(url_for('login_page'))
        else:
            flash(msg, "danger")

    return render_template('student_signup.html')

@app.route('/staff/signup', methods=['GET', 'POST'])
def staff_signup_page():
    if request.method == 'POST':
        staff_id = request.form.get('staff_id', '').strip()
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        department = request.form.get('department', '').strip()

        success, msg = register_staff_account(staff_id, name, email, password, department)
        if success:
            flash(msg, "success")
            return redirect(url_for('login_page'))
        else:
            flash(msg, "danger")

    return render_template('staff_signup.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login_page'))

# --- DASHBOARD & FUNCTIONAL PAGES ---

@app.route('/student/dashboard')
@student_required
def student_dashboard():
    student_id = session['user_id']
    student = get_student_by_id(student_id)
    summary = get_student_attendance_summary(student_id)
    notifications = get_student_notifications(student_id, limit=5)
    
    return render_template(
        'student_dashboard.html',
        student=student,
        summary=summary,
        notifications=notifications
    )

@app.route('/student/attendance')
@student_required
def student_attendance_page():
    student_id = session['user_id']
    student = get_student_by_id(student_id)
    active_sessions = get_active_sessions_for_class(student['department'], student['year'], student['section'])
    
    return render_template(
        'student_attendance.html',
        student=student,
        active_sessions=active_sessions
    )

@app.route('/staff/dashboard')
@staff_required
def staff_dashboard():
    staff_id = session['user_id']
    staff = get_staff_by_id(staff_id)
    today_day = get_today_day_name()
    allocations = get_staff_allocations(staff_id, day=today_day)
    all_allocations = get_staff_allocations(staff_id)

    return render_template(
        'staff_dashboard.html',
        staff=staff,
        allocations=allocations,
        all_allocations=all_allocations
    )

@app.route('/staff/attendance')
@staff_required
def staff_attendance_page():
    staff_id = session['user_id']
    session_id = request.args.get('session_id', type=int)
    active_session = get_active_session(session_id) if session_id else None

    return render_template(
        'staff_attendance.html',
        active_session=active_session
    )

@app.route('/students')
@staff_required
def students_page():
    staff_id = session['user_id']
    staff = get_staff_by_id(staff_id)
    
    # Default search for staff department, Year 4, Sec C
    dept = request.args.get('department', staff['department'])
    year = request.args.get('year', 4, type=int)
    section = request.args.get('section', 'C')

    students_list = get_students_by_class(dept, year, section)

    # Attach attendance summary for each student
    for st in students_list:
        summary = get_student_attendance_summary(st['student_id'])
        st['attendance_pct'] = summary['percentage']
        st['present_cnt'] = summary['present']
        st['total_cnt'] = summary['total_classes']

    return render_template(
        'students.html',
        students=students_list,
        selected_dept=dept,
        selected_year=year,
        selected_sec=section
    )

@app.route('/timetable')
@login_required
def timetable_page():
    if session['role'] == 'STUDENT':
        student = get_student_by_id(session['user_id'])
        timetable_data = get_student_timetable_status(session['user_id'], student['department'], student['year'], student['section'])
        return render_template('timetable.html', timetable=timetable_data)
    else:
        staff_id = session['user_id']
        allocations = get_staff_allocations(staff_id)
        return render_template('timetable.html', staff_allocations=allocations)

@app.route('/reports')
@login_required
def reports_page():
    return render_template('reports.html')

# --- API ENDPOINTS ---

@app.route('/api/student-timetable', methods=['GET'])
@student_required
def api_student_timetable():
    student_id = session.get('user_id')
    student = get_student_by_id(student_id)
    if not student:
        return format_json_response(False, "Student record not found.", status_code=404)

    day = request.args.get('day', get_today_day_name())
    data = get_student_timetable_status(student_id, student['department'], student['year'], student['section'], day=day)
    
    return format_json_response(True, "Student timetable retrieved successfully.", data=data)

@app.route('/api/student-attendance-summary', methods=['GET'])
@student_required
def api_student_attendance_summary():
    student_id = session.get('user_id')
    summary = get_student_attendance_summary(student_id)
    return format_json_response(True, "Summary retrieved.", data=summary)

@app.route('/api/student-course-attendance', methods=['GET'])
@student_required
def api_student_course_attendance():
    student_id = session.get('user_id')
    courses = get_student_course_attendance(student_id)
    return format_json_response(True, "Course-wise data retrieved.", data=courses)

@app.route('/api/student-daily-attendance', methods=['GET'])
@student_required
def api_student_daily_attendance():
    student_id = session.get('user_id')
    daily = get_student_daily_attendance(student_id)
    return format_json_response(True, "Daily attendance data retrieved.", data=daily)

@app.route('/api/student-weekly-attendance', methods=['GET'])
@student_required
def api_student_weekly_attendance():
    student_id = session.get('user_id')
    weekly = get_student_weekly_attendance(student_id)
    return format_json_response(True, "Weekly attendance data retrieved.", data=weekly)

@app.route('/api/register-face', methods=['POST'])
@student_required
def api_register_face():
    student_id = session.get('user_id')
    data = request.get_json() or {}
    images_base64 = data.get('images', [])

    if not images_base64:
        return format_json_response(False, "No face images provided.")

    image_frames = []
    for b64 in images_base64:
        img = decode_base64_image(b64)
        if img is not None:
            image_frames.append(img)

    if not image_frames:
        return format_json_response(False, "Failed to decode submitted face images.")

    success, msg, count = register_student_face_samples(student_id, image_frames)
    if success:
        return format_json_response(True, msg, data={"samples_registered": count})
    else:
        return format_json_response(False, msg, status_code=400)

@app.route('/api/mark-self-attendance', methods=['POST'])
@student_required
def api_mark_self_attendance():
    logged_in_student_id = session.get('user_id')
    data = request.get_json() or {}
    image_b64 = data.get('image', '')
    session_id = data.get('session_id')

    if not image_b64 or not session_id:
        return format_json_response(False, "Missing webcam image or attendance session ID.")

    active_session = get_active_session(session_id)
    if not active_session or active_session['status'] != 'ACTIVE':
        return format_json_response(False, "Selected attendance session is closed or inactive.")

    img = decode_base64_image(image_b64)
    if img is None:
        return format_json_response(False, "Invalid image data.")

    # Run Face Recognition
    rec_result = recognize_face(img)
    if not rec_result['matched']:
        return format_json_response(False, f"Facial verification failed: {rec_result['message']}")

    recognized_student_id = rec_result['student_id']

    # Security Guard: Prevent Student A from marking attendance for Student B
    if recognized_student_id != logged_in_student_id:
        return format_json_response(False, "Security Violation: Captured face does not match the logged-in student account.", status_code=403)

    # Mark Attendance
    success, msg = mark_attendance(
        student_id=logged_in_student_id,
        session_id=session_id,
        staff_id=active_session['staff_id'],
        department=active_session['department'],
        year=active_session['year'],
        section=active_session['section'],
        subject=active_session['subject'],
        hour=active_session['hour']
    )

    if success:
        return format_json_response(True, msg, data=rec_result)
    else:
        return format_json_response(False, msg)

@app.route('/api/staff/start-session', methods=['POST'])
@staff_required
def api_staff_start_session():
    staff_id = session.get('user_id')
    data = request.get_json() or {}

    department = data.get('department')
    year = data.get('year')
    section = data.get('section')
    day = data.get('day', get_today_day_name())
    subject = data.get('subject')
    hour = data.get('hour')

    if not department or not year or not section or not subject or not hour:
        return format_json_response(False, "Missing class allocation parameters.")

    success, msg, session_id = start_attendance_session(staff_id, department, year, section, day, subject, hour)
    if success:
        return format_json_response(True, msg, data={"session_id": session_id})
    else:
        return format_json_response(False, msg, status_code=400)

@app.route('/api/staff/stop-session', methods=['POST'])
@staff_required
def api_staff_stop_session():
    staff_id = session.get('user_id')
    data = request.get_json() or {}
    session_id = data.get('session_id')

    if not session_id:
        return format_json_response(False, "Session ID is required.")

    success, msg = stop_attendance_session(session_id, staff_id)
    return format_json_response(success, msg)

@app.route('/api/staff/live-recognize', methods=['POST'])
@staff_required
def api_staff_live_recognize():
    staff_id = session.get('user_id')
    data = request.get_json() or {}

    session_id = data.get('session_id')
    image_b64 = data.get('image')

    if not session_id or not image_b64:
        return format_json_response(False, "Session ID and image frame required.")

    active_session = get_active_session(session_id)
    if not active_session or active_session['status'] != 'ACTIVE':
        return format_json_response(False, "Attendance session is not active.")

    if active_session['staff_id'] != staff_id:
        return format_json_response(False, "Unauthorized: You do not manage this session.", status_code=403)

    img = decode_base64_image(image_b64)
    if img is None:
        return format_json_response(False, "Invalid camera frame.")

    # Recognize Face
    rec_result = recognize_face(img)
    if not rec_result['matched']:
        return format_json_response(False, rec_result['message'], data=rec_result)

    recognized_id = rec_result['student_id']

    # Verify student class matches session class
    if (rec_result['department'] != active_session['department'] or
        int(rec_result['year']) != int(active_session['year']) or
        rec_result['section'] != active_session['section']):
        return format_json_response(False, f"Recognized student {rec_result['name']} ({recognized_id}) does not belong to {active_session['department']} Year {active_session['year']} Sec {active_session['section']}.", data=rec_result)

    # Attempt marking attendance
    success, msg = mark_attendance(
        student_id=recognized_id,
        session_id=session_id,
        staff_id=active_session['staff_id'],
        department=active_session['department'],
        year=active_session['year'],
        section=active_session['section'],
        subject=active_session['subject'],
        hour=active_session['hour']
    )

    rec_result['attendance_success'] = success
    rec_result['attendance_message'] = msg

    return format_json_response(success, msg, data=rec_result)

@app.route('/api/staff/session-attendance/<int:session_id>', methods=['GET'])
@staff_required
def api_staff_session_attendance(session_id):
    records = get_session_attendance_list(session_id)
    return format_json_response(True, "Session attendance retrieved.", data=records)

@app.route('/api/notifications', methods=['GET'])
@student_required
def api_get_notifications():
    student_id = session.get('user_id')
    notifs = get_student_notifications(student_id)
    return format_json_response(True, "Notifications retrieved.", data=notifs)

@app.route('/api/notifications/read', methods=['POST'])
@student_required
def api_mark_notification_read():
    student_id = session.get('user_id')
    data = request.get_json() or {}
    notif_id = data.get('notification_id')
    
    if notif_id:
        mark_notification_read(notif_id, student_id)
    return format_json_response(True, "Notification marked as read.")

@app.route('/api/export-pdf-report', methods=['GET'])
@student_required
def api_export_pdf_report():
    student_id = session.get('user_id')
    filepath = generate_student_pdf_report(student_id)
    
    if filepath and os.path.exists(filepath):
        return send_file(filepath, as_attachment=True, download_name=f"Attendance_Report_{student_id}.pdf")
    else:
        return format_json_response(False, "Failed to generate PDF report.", status_code=500)

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error_code=404, error_message="The requested page or endpoint was not found."), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error_code=500, error_message="An internal server error occurred. Please try again."), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
