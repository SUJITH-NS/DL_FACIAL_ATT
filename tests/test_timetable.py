import unittest
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils import get_current_timetable_hour, is_break_time

class TestTimetable(unittest.TestCase):

    def test_hour_resolution(self):
        # 09:00 AM -> Hour 1
        dt1 = datetime(2026, 8, 25, 9, 0, 0)
        self.assertEqual(get_current_timetable_hour(dt1), 1)

        # 11:00 AM -> Hour 3
        dt3 = datetime(2026, 8, 25, 11, 0, 0)
        self.assertEqual(get_current_timetable_hour(dt3), 3)

        # 10:30 AM -> Morning Break
        dt_break = datetime(2026, 8, 25, 10, 30, 0)
        self.assertIsNone(get_current_timetable_hour(dt_break))
        self.assertTrue(is_break_time(dt_break))

        # 12:45 PM -> Lunch Break
        dt_lunch = datetime(2026, 8, 25, 12, 45, 0)
        self.assertIsNone(get_current_timetable_hour(dt_lunch))
        self.assertTrue(is_break_time(dt_lunch))

if __name__ == '__main__':
    unittest.main()
