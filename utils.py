import base64
from datetime import datetime, time
import re
from flask import jsonify, make_response
import numpy as np
import cv2

from config import Config


def get_today_day_name(dt=None):
    """
    Returns today's day of week name (e.g. 'Monday', 'Tuesday').
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%A")

def get_current_timetable_hour(dt=None):
    """
    Evaluates datetime and returns the matching timetable hour (1..7)
    or None if current time falls in break time or outside college hours.
    """
    if dt is None:
        dt = datetime.now()

    current_time = dt.time()

    for hour, (start_str, end_str) in Config.TIMETABLE.items():
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        
        start_t = time(sh, sm)
        end_t = time(eh, em)

        if start_t <= current_time < end_t:
            return hour

    return None

def is_break_time(dt=None):
    """
    Checks if current time falls during scheduled break intervals.
    """
    if dt is None:
        dt = datetime.now()

    current_time = dt.time()

    for start_str, end_str in Config.BREAK_TIMES:
        sh, sm = map(int, start_str.split(":"))
        eh, em = map(int, end_str.split(":"))
        if time(sh, sm) <= current_time < time(eh, em):
            return True

    return False

def format_json_response(success, message, data=None, status_code=200):
    """
    Creates a standard consistent API JSON response format across all endpoints.
    """
    payload = {
        "success": success,
        "message": message
    }
    if data is not None:
        payload["data"] = data

    return make_response(jsonify(payload), status_code)

def decode_base64_image(base64_string):
    """
    Decodes a base64 encoded image string (e.g. data:image/jpeg;base64,...)
    into an OpenCV BGR image array.
    """
    try:
        if "," in base64_string:
            base64_string = base64_string.split(",")[1]
        
        img_bytes = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"[IMAGE DECODE ERROR] {e}")
        return None

def validate_email(email):
    """
    Validates email syntax format using regex.
    """
    pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
    return re.match(pattern, email) is not None
