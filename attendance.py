from datetime import datetime
import pymysql

from config import Config
from database import execute_query, create_notification, log_audit
from utils import get_current_timetable_hour, get_today_day_name


# --- SESSION MANAGEMENT FUNCTIONS ---

def auto_complete_expired_sessions():
    """
    Checks all ACTIVE attendance sessions in MySQL.
    If the current datetime has reached or passed the session's timetable period end time,
    the session is automatically updated to COMPLETED and finalized.
    This operation is strictly idempotent (only ACTIVE sessions can be updated).
    """
    now = datetime.now()
    active_sessions_sql = "SELECT * FROM attendance_sessions WHERE status = 'ACTIVE'"
    active_sessions = execute_query(active_sessions_sql, fetchall=True) or []

    for sess in active_sessions:
        hour = sess.get('hour')
        session_date = sess.get('session_date')
        if not hour or not session_date:
            continue

        start_time_str, end_time_str = Config.TIMETABLE.get(int(hour), (None, None))
        if not end_time_str:
            continue

        try:
            date_str = str(session_date)
            end_dt_str = f"{date_str} {end_time_str}:00"
            period_end_dt = datetime.strptime(end_dt_str, "%Y-%m-%d %H:%M:%S")

            if now >= period_end_dt:
                update_sql = """
                UPDATE attendance_sessions
                SET status = 'COMPLETED', end_time = %s
                WHERE session_id = %s AND status = 'ACTIVE'
                """
                affected = execute_query(update_sql, (f"{end_time_str}:00", sess['session_id']))
                if affected and affected > 0:
                    log_audit(sess['staff_id'], 'SYSTEM', f"Auto-completed expired attendance session {sess['session_id']} (Hour {hour})")
        except Exception as e:
            print(f"[AUTO COMPLETE SESSIONS ERROR] Session {sess.get('session_id')}: {e}")

def start_attendance_session(staff_id, department, year, section, day, subject, hour):
    """
    Validates rules and creates a new ACTIVE attendance session.
    """
    auto_complete_expired_sessions()
    today_day = get_today_day_name()
    current_hour = get_current_timetable_hour()
    today_date = datetime.now().strftime("%Y-%m-%d")
    current_time_str = datetime.now().strftime("%H:%M:%S")

    # 1. Day validation
    if day.lower() != today_day.lower():
        return False, f"Cannot start session for {day}. Today is {today_day}.", None

    # 2. Timetable hour validation
    if current_hour is None:
        return False, "Attendance cannot be started during break time or outside college hours.", None

    if current_hour != int(hour):
        return False, f"You selected Hour {hour}, but the current timetable hour is Hour {current_hour}.", None

    # 3. Allocation ownership validation
    alloc_sql = """
    SELECT * FROM staff_class_allocation
    WHERE staff_id = %s AND department = %s AND year = %s AND section = %s AND day = %s AND hour = %s
    """
    alloc = execute_query(alloc_sql, (staff_id, department, year, section, day, hour), fetchone=True)
    if not alloc:
        return False, f"No allocation found for staff {staff_id} for {department} Year {year} Sec {section} Hour {hour}.", None

    # 4. Prevent duplicate active session for department + year + section + hour + date
    conflict_sql = """
    SELECT * FROM attendance_sessions
    WHERE department = %s AND year = %s AND section = %s AND hour = %s AND session_date = %s AND status = 'ACTIVE'
    """
    conflict = execute_query(conflict_sql, (department, year, section, hour, today_date), fetchone=True)
    if conflict:
        if conflict['staff_id'] == staff_id:
            return True, "Active session already in progress for this class.", conflict['session_id']
        else:
            return False, f"Another active session for this class is already running by staff {conflict['staff_id']}.", None

    # 5. Insert active session record
    insert_sql = """
    INSERT INTO attendance_sessions (staff_id, department, year, section, day, subject, hour, session_date, start_time, status)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'ACTIVE')
    """
    session_id = execute_query(insert_sql, (staff_id, department, year, section, day, subject, hour, today_date, current_time_str))

    log_audit(staff_id, 'STAFF', f"Started attendance session {session_id} for {subject} Hour {hour}")
    return True, f"Attendance session started successfully for {subject} - Hour {hour}.", session_id

def stop_attendance_session(session_id, staff_id):
    """
    Closes an active attendance session.
    """
    auto_complete_expired_sessions()
    current_time_str = datetime.now().strftime("%H:%M:%S")
    sql = """
    UPDATE attendance_sessions
    SET status = 'COMPLETED', end_time = %s
    WHERE session_id = %s AND staff_id = %s AND status = 'ACTIVE'
    """
    res = execute_query(sql, (current_time_str, session_id, staff_id))
    log_audit(staff_id, 'STAFF', f"Stopped attendance session {session_id}")
    return True, "Attendance session closed successfully."

def get_active_session(session_id):
    auto_complete_expired_sessions()
    sql = "SELECT * FROM attendance_sessions WHERE session_id = %s"
    return execute_query(sql, (session_id,), fetchone=True)

def get_active_sessions_for_class(department, year, section):
    auto_complete_expired_sessions()
    today_date = datetime.now().strftime("%Y-%m-%d")
    sql = """
    SELECT * FROM attendance_sessions
    WHERE department = %s AND year = %s AND section = %s AND session_date = %s AND status = 'ACTIVE'
    """
    return execute_query(sql, (department, year, section, today_date), fetchall=True)

def get_session_attendance_list(session_id):
    sql = """
    SELECT a.*, s.name as student_name
    FROM attendance a
    JOIN students s ON a.student_id = s.student_id
    WHERE a.session_id = %s
    ORDER BY a.attendance_time DESC
    """
    return execute_query(sql, (session_id,), fetchall=True)

# --- ATTENDANCE MARKING FUNCTIONS ---

def is_attendance_marked(student_id, session_id):
    sql = "SELECT id FROM attendance WHERE student_id = %s AND session_id = %s"
    res = execute_query(sql, (student_id, session_id), fetchone=True)
    return res is not None

def mark_attendance(student_id, session_id, staff_id, department, year, section, subject, hour):
    """
    Validates guards and inserts attendance record into MySQL.
    """
    auto_complete_expired_sessions()
    session_rec = get_active_session(session_id)
    if not session_rec or session_rec['status'] != 'ACTIVE':
        return False, "Attendance session is not active or has been closed."

    current_hour = get_current_timetable_hour()
    if current_hour != session_rec['hour']:
        return False, f"Current timetable hour (Hour {current_hour}) does not match session hour (Hour {session_rec['hour']})."

    if is_attendance_marked(student_id, session_id):
        return False, "Attendance already marked for this session."

    today_date = datetime.now().strftime("%Y-%m-%d")
    current_time_str = datetime.now().strftime("%H:%M:%S")

    sql = """
    INSERT INTO attendance (student_id, session_id, attendance_date, attendance_time, status, subject, hour, staff_id, department, year, section)
    VALUES (%s, %s, %s, %s, 'PRESENT', %s, %s, %s, %s, %s, %s)
    """
    try:
        execute_query(sql, (student_id, session_id, today_date, current_time_str, subject, hour, staff_id, department, year, section))
        
        # Send Notification to Student
        notif_msg = f"Attendance marked Present for {subject} - Hour {hour} on {today_date}."
        create_notification(student_id, notif_msg)

        log_audit(student_id, 'STUDENT', f"Attendance marked Present for session {session_id}")
        return True, f"Attendance marked Present for {subject} - Hour {hour}."
    except pymysql.err.IntegrityError:
        return False, "Attendance already marked for this student."
    except Exception as e:
        return False, f"Failed to record attendance: {e}"

# --- TIMETABLE & STATUS LOGIC ---

def get_student_timetable_status(student_id, department, year, section, day=None):
    """
    Generates dynamic status (PRESENT, ABSENT, ONGOING, UPCOMING) for today's classes.
    """
    auto_complete_expired_sessions()
    if day is None:
        day = get_today_day_name()

    today_date = datetime.now().strftime("%Y-%m-%d")
    current_hour = get_current_timetable_hour()

    # Get class allocations for student's class
    alloc_sql = """
    SELECT a.*, st.name as staff_name
    FROM staff_class_allocation a
    JOIN staff st ON a.staff_id = st.staff_id
    WHERE a.department = %s AND a.year = %s AND a.section = %s AND a.day = %s
    ORDER BY a.hour ASC
    """
    allocations = execute_query(alloc_sql, (department, year, section, day), fetchall=True)

    result_classes = []

    for alloc in allocations:
        h = alloc['hour']
        start_t, end_t = Config.TIMETABLE.get(h, ("00:00", "00:00"))

        # Find active or closed sessions for this class and hour
        sess_sql = """
        SELECT * FROM attendance_sessions
        WHERE department = %s AND year = %s AND section = %s AND day = %s AND hour = %s AND session_date = %s
        ORDER BY session_id DESC LIMIT 1
        """
        sess = execute_query(sess_sql, (department, year, section, day, h, today_date), fetchone=True)

        status = "UPCOMING"
        can_mark = False
        session_id = None

        if sess:
            session_id = sess['session_id']
            # Check if student has attendance record for this session
            att_marked = is_attendance_marked(student_id, session_id)

            if att_marked:
                status = "PRESENT"
            elif sess['status'] == 'ACTIVE':
                status = "ONGOING"
                can_mark = True
            elif sess['status'] in ('CLOSED', 'COMPLETED'):
                status = "ABSENT"
        else:
            # No session created yet
            if current_hour is not None:
                if h == current_hour:
                    status = "UPCOMING"
                elif h < current_hour:
                    status = "ABSENT" # Passed class without session creation
                else:
                    status = "UPCOMING"
            else:
                status = "UPCOMING"

        result_classes.append({
            "hour": h,
            "subject": alloc['subject'],
            "staff_name": alloc['staff_name'],
            "start_time": start_t,
            "end_time": end_t,
            "status": status,
            "can_mark": can_mark,
            "session_id": session_id
        })

    return {
        "day": day,
        "date": today_date,
        "classes": result_classes
    }

# --- REPORT CALCULATION FUNCTIONS ---

def get_student_attendance_summary(student_id):
    """
    Consolidated Summary based on CLOSED/COMPLETED sessions.
    """
    auto_complete_expired_sessions()
    student_sql = "SELECT department, year, section FROM students WHERE student_id = %s"
    student = execute_query(student_sql, (student_id,), fetchone=True)
    if not student:
        return {"total_classes": 0, "present": 0, "absent": 0, "percentage": 0.0}

    dept, yr, sec = student['department'], student['year'], student['section']

    # Total completed classes = count of CLOSED or COMPLETED sessions for class
    total_sql = """
    SELECT COUNT(*) as cnt FROM attendance_sessions
    WHERE department = %s AND year = %s AND section = %s AND status IN ('CLOSED', 'COMPLETED')
    """
    tot_res = execute_query(total_sql, (dept, yr, sec), fetchone=True)
    total_classes = tot_res['cnt'] if tot_res else 0

    # Present count
    pres_sql = """
    SELECT COUNT(DISTINCT a.session_id) as cnt
    FROM attendance a
    JOIN attendance_sessions s ON a.session_id = s.session_id
    WHERE a.student_id = %s AND s.status IN ('CLOSED', 'COMPLETED')
    """
    pres_res = execute_query(pres_sql, (student_id,), fetchone=True)
    present_cnt = pres_res['cnt'] if pres_res else 0

    absent_cnt = max(0, total_classes - present_cnt)
    percentage = round((present_cnt / total_classes * 100.0), 2) if total_classes > 0 else 0.0

    return {
        "total_classes": total_classes,
        "present": present_cnt,
        "absent": absent_cnt,
        "percentage": percentage
    }

def get_student_course_attendance(student_id):
    """
    Subject-wise Attendance Breakdown based on CLOSED/COMPLETED sessions.
    """
    auto_complete_expired_sessions()
    student_sql = "SELECT department, year, section FROM students WHERE student_id = %s"
    student = execute_query(student_sql, (student_id,), fetchone=True)
    if not student:
        return []

    dept, yr, sec = student['department'], student['year'], student['section']

    sql = """
    SELECT s.subject,
           COUNT(s.session_id) as total_classes,
           SUM(CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END) as present
    FROM attendance_sessions s
    LEFT JOIN attendance a ON s.session_id = a.session_id AND a.student_id = %s
    WHERE s.department = %s AND s.year = %s AND s.section = %s AND s.status IN ('CLOSED', 'COMPLETED')
    GROUP BY s.subject
    """
    records = execute_query(sql, (student_id, dept, yr, sec), fetchall=True)

    courses = []
    for r in records:
        tot = r['total_classes']
        pres = int(r['present'] or 0)
        absent = tot - pres
        pct = round((pres / tot * 100.0), 2) if tot > 0 else 0.0
        courses.append({
            "subject": r['subject'],
            "total_classes": tot,
            "present": pres,
            "absent": absent,
            "percentage": pct
        })

    return courses

def get_student_daily_attendance(student_id):
    """
    Date-wise Daily Attendance Breakdown.
    """
    auto_complete_expired_sessions()
    student_sql = "SELECT department, year, section FROM students WHERE student_id = %s"
    student = execute_query(student_sql, (student_id,), fetchone=True)
    if not student:
        return []

    dept, yr, sec = student['department'], student['year'], student['section']

    sql = """
    SELECT s.session_date,
           s.day,
           COUNT(s.session_id) as total_classes,
           SUM(CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END) as present
    FROM attendance_sessions s
    LEFT JOIN attendance a ON s.session_id = a.session_id AND a.student_id = %s
    WHERE s.department = %s AND s.year = %s AND s.section = %s AND s.status IN ('CLOSED', 'COMPLETED')
    GROUP BY s.session_date, s.day
    ORDER BY s.session_date DESC
    """
    records = execute_query(sql, (student_id, dept, yr, sec), fetchall=True)

    daily = []
    for r in records:
        tot = r['total_classes']
        pres = int(r['present'] or 0)
        absent = tot - pres
        pct = round((pres / tot * 100.0), 2) if tot > 0 else 0.0
        daily.append({
            "date": str(r['session_date']),
            "day": r['day'],
            "total_classes": tot,
            "present": pres,
            "absent": absent,
            "percentage": pct
        })

    return daily

def get_student_weekly_attendance(student_id):
    """
    Week-wise Attendance Breakdown.
    """
    auto_complete_expired_sessions()
    student_sql = "SELECT department, year, section FROM students WHERE student_id = %s"
    student = execute_query(student_sql, (student_id,), fetchone=True)
    if not student:
        return []

    dept, yr, sec = student['department'], student['year'], student['section']

    sql = """
    SELECT YEARWEEK(s.session_date, 1) as week_num,
           MIN(s.session_date) as week_start,
           MAX(s.session_date) as week_end,
           COUNT(s.session_id) as total_classes,
           SUM(CASE WHEN a.id IS NOT NULL THEN 1 ELSE 0 END) as present
    FROM attendance_sessions s
    LEFT JOIN attendance a ON s.session_id = a.session_id AND a.student_id = %s
    WHERE s.department = %s AND s.year = %s AND s.section = %s AND s.status IN ('CLOSED', 'COMPLETED')
    GROUP BY YEARWEEK(s.session_date, 1)
    ORDER BY week_num DESC
    """
    records = execute_query(sql, (student_id, dept, yr, sec), fetchall=True)

    weekly = []
    for r in records:
        tot = r['total_classes']
        pres = int(r['present'] or 0)
        absent = tot - pres
        pct = round((pres / tot * 100.0), 2) if tot > 0 else 0.0
        weekly.append({
            "week": f"Week ({r['week_start']} to {r['week_end']})",
            "total_classes": tot,
            "present": pres,
            "absent": absent,
            "percentage": pct
        })

    return weekly
