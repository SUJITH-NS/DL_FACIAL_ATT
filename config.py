import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = int(os.getenv('DB_PORT', 3306))
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'Nanthitha@123')
    DB_NAME = os.getenv('DB_NAME', 'facial_attendance')

    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY', 'super_secret_facial_attendance_key_2026')

    # AI Recognition Configuration
    RECOGNITION_THRESHOLD = float(os.getenv('RECOGNITION_THRESHOLD', 0.70))
    MIN_FACE_SIZE = (80, 80)
    SAMPLES_PER_STUDENT = 10

    # Project Directories
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    STUDENT_IMAGES_DIR = os.path.join(BASE_DIR, 'images', 'students')
    REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
    EMBEDDINGS_DIR = os.path.join(BASE_DIR, 'embeddings')
    MODELS_DIR = os.path.join(BASE_DIR, 'models')

    # Shared Timetable Definition (7 Hours + Breaks)
    # Format: hour_number: (start_time_str, end_time_str)
    TIMETABLE = {
        1: ("08:45", "09:35"),
        2: ("09:35", "10:25"),
        # Break 1: 10:25 - 10:45
        3: ("10:45", "11:35"),
        4: ("11:35", "12:25"),
        # Lunch Break: 12:25 - 13:25
        5: ("13:25", "14:15"),
        6: ("14:15", "15:05"),
        # Break 2: 15:05 - 15:25
        7: ("15:25", "16:15")
    }

    BREAK_TIMES = [
        ("10:25", "10:45"), # Morning Break
        ("12:25", "13:25"), # Lunch Break
        ("15:05", "15:25")  # Afternoon Break
    ]

# Ensure directories exist
for path in [Config.STUDENT_IMAGES_DIR, Config.REPORTS_DIR, Config.EMBEDDINGS_DIR, Config.MODELS_DIR]:
    os.makedirs(path, exist_ok=True)
