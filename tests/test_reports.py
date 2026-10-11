import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from attendance import get_student_attendance_summary, get_student_course_attendance

class TestReports(unittest.TestCase):

    def test_student_summary_calculation(self):
        summary = get_student_attendance_summary("23CSR001")
        self.assertIn("total_classes", summary)
        self.assertIn("present", summary)
        self.assertIn("absent", summary)
        self.assertIn("percentage", summary)
        self.assertIsInstance(summary["percentage"], float)

    def test_student_course_attendance(self):
        courses = get_student_course_attendance("23CSR001")
        self.assertIsInstance(courses, list)

if __name__ == '__main__':
    unittest.main()
