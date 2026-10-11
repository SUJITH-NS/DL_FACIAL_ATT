import unittest
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database import get_student_by_id, get_staff_by_id, execute_query
from attendance import (
    is_attendance_marked, stop_attendance_session, auto_complete_expired_sessions,
    get_active_sessions_for_class, get_student_attendance_summary
)
from utils import get_current_timetable_hour

class TestAttendance(unittest.TestCase):

    def test_database_seeded_records(self):
        student = get_student_by_id("23CSR001")
        self.assertIsNotNone(student)
        self.assertEqual(student['name'], "NANTHITHA P")

        staff = get_staff_by_id("CSE001")
        self.assertIsNotNone(staff)
        self.assertEqual(staff['name'], "Dr. Alan Turing")

    def test_is_attendance_marked_nonexistent(self):
        marked = is_attendance_marked("23CSR001", 999999)
        self.assertFalse(marked)

    def test_manual_stop_session(self):
        today_date = datetime.now().strftime("%Y-%m-%d")
        cur_h = get_current_timetable_hour() or 6
        sql = """
        INSERT INTO attendance_sessions (staff_id, department, year, section, day, subject, hour, session_date, start_time, status)
        VALUES ('CSE001', 'CSE', 4, 'C', 'Tuesday', 'Computer Vision', %s, %s, '14:15:00', 'ACTIVE')
        """
        session_id = execute_query(sql, (cur_h, today_date))
        
        # Verify active (since period end 15:05 is in future)
        actives = get_active_sessions_for_class('CSE', 4, 'C')
        active_ids = [s['session_id'] for s in actives]
        self.assertIn(session_id, active_ids)

        # Stop manually
        stop_attendance_session(session_id, 'CSE001')

        # Verify no longer active and status is COMPLETED
        actives_after = get_active_sessions_for_class('CSE', 4, 'C')
        active_ids_after = [s['session_id'] for s in actives_after]
        self.assertNotIn(session_id, active_ids_after)

        sess_rec = execute_query("SELECT * FROM attendance_sessions WHERE session_id = %s", (session_id,), fetchone=True)
        self.assertEqual(sess_rec['status'], 'COMPLETED')

    def test_automatic_session_completion_and_idempotency(self):
        summary_before = get_student_attendance_summary('23CSR001')

        # Insert active session with past session_date (e.g. yesterday) so period end time is in past
        past_date = "2026-01-01"
        sql = """
        INSERT INTO attendance_sessions (staff_id, department, year, section, day, subject, hour, session_date, start_time, status)
        VALUES ('CSE001', 'CSE', 4, 'C', 'Monday', 'Machine Learning', 1, %s, '08:45:00', 'ACTIVE')
        """
        session_id = execute_query(sql, (past_date,))

        # Trigger auto completion
        auto_complete_expired_sessions()

        summary_after_first = get_student_attendance_summary('23CSR001')
        self.assertEqual(summary_after_first['total_classes'], summary_before['total_classes'] + 1)

        sess_rec = execute_query("SELECT * FROM attendance_sessions WHERE session_id = %s", (session_id,), fetchone=True)
        self.assertEqual(sess_rec['status'], 'COMPLETED')

        # Trigger auto completion multiple times to verify NO double counting
        auto_complete_expired_sessions()
        auto_complete_expired_sessions()

        summary_after_multiple = get_student_attendance_summary('23CSR001')
        self.assertEqual(summary_after_multiple['total_classes'], summary_after_first['total_classes'])

if __name__ == '__main__':
    unittest.main()
