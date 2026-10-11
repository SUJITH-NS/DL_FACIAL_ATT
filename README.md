# FACIAL ATTENDANCE REGISTRATION AND MANAGEMENT SYSTEM

An AI-based facial recognition attendance management web application built with Python Flask, MySQL 8, OpenCV, MTCNN/MobileNet face embeddings, and a modern responsive UI system.

---

## 1. PROJECT DESCRIPTION
This system automates individual identification and attendance logging using real-time facial feature extraction and cosine similarity matching. It replaces manual registers, eliminates proxy entries, and provides automated reporting for students and faculty.

---

## 2. TECHNOLOGY STACK
- **Frontend**: HTML5, CSS3 (Vanilla Responsive Design System), JavaScript (ES6+ webcam API)
- **Backend**: Python 3.10, Flask 3.0.0
- **Database**: MySQL 8.0 (PyMySQL connection layer)
- **AI / Face Recognition**: OpenCV 4.8, MTCNN, TensorFlow / MobileNetV2 feature embeddings, scikit-learn cosine similarity
- **Authentication**: Flask Session management, Werkzeug scrypt password hashing, role-based access decorators
- **Reporting**: ReportLab PDF Generation & HTML printable data tables

---

## 3. PROJECT STRUCTURE
```
FacialAttendance/
│
├── app.py                      # Flask main entrypoint & web routes
├── database.py                 # MySQL 8 database connections & query functions
├── attendance.py               # Attendance tracking, status calculations & sessions
├── recognition.py              # Face embedding comparison & cosine similarity engine
├── face_registration.py        # Multi-sample face capture & embedding storage logic
├── face_detector.py            # OpenCV / MTCNN face quality check & bounding box detection
├── auth.py                     # Authentication decorators, password hashing & session management
├── utils.py                    # Timetable calculations, helpers & JSON formatters
├── config.py                   # Centralized configuration (Timetable hours, DB settings)
├── pdf_generator.py            # ReportLab PDF report builder
├── requirements.txt            # Python dependencies
├── README.md                   # Setup instructions and system documentation
├── .env                        # Local environment variables
├── .env.example                # Example environment template
│
├── models/                     # Face model files
├── embeddings/                 # Serialized embeddings storage
├── images/
│   └── students/               # Registered student sample images
├── reports/                    # Generated PDF reports output folder
│
├── static/
│   ├── css/
│   │   └── style.css           # Global unified design system
│   ├── js/
│   │   └── app.js             # Webcam stream, live facial recognition, API integration
│   └── images/
│
├── templates/
│   ├── base.html               # Shared base layout
│   ├── login.html              # Login page (Student/Staff)
│   ├── student_signup.html     # Student registration page
│   ├── staff_signup.html       # Staff registration page
│   ├── student_dashboard.html   # Student main dashboard
│   ├── student_attendance.html  # Student self facial attendance
│   ├── staff_dashboard.html     # Staff allocations & session management
│   ├── staff_attendance.html   # Staff live facial recognition stream
│   ├── students.html           # Staff class roster viewer
│   ├── timetable.html          # Interactive timetable grid view
│   ├── reports.html            # Consolidated, course, daily & weekly reports
│   └── error.html              # Unified error fallback page
│
├── database/
│   ├── schema.sql              # MySQL DDL schema
│   └── seed.sql                # Seed data for staff (CSE001-CSE011), students, allocations
│
└── tests/
    ├── test_auth.py            # Auth unit tests
    ├── test_attendance.py      # Attendance logic tests
    ├── test_timetable.py       # Timetable resolution tests
    └── test_reports.py         # Attendance percentage tests
```

---

## 4. SETUP & INSTALLATION INSTRUCTIONS

### Step 1: Install Python Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: MySQL Database Setup
Ensure MySQL 8 is running locally on port `3306`.
Create or copy `.env` from `.env.example`:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=Nanthitha@123
DB_NAME=facial_attendance
SECRET_KEY=super_secret_facial_attendance_key_2026
RECOGNITION_THRESHOLD=0.70
```

Run schema and seed initialization:
```bash
python -c "
import pymysql
conn = pymysql.connect(host='localhost', user='root', password='Nanthitha@123', port=3306, autocommit=True)
cursor = conn.cursor()
for f in ['database/schema.sql', 'database/seed.sql']:
    with open(f, 'r', encoding='utf-8') as sql_file:
        stmts = [s.strip() for s in sql_file.read().split(';') if s.strip()]
        for s in stmts:
            cursor.execute(s)
conn.close()
print('Database initialized successfully!')
"
```

### Step 3: Run the Application
```bash
python app.py
```
Open your browser at `http://localhost:5000`.

---

## 5. USER WORKFLOW GUIDE

### A. How to Register a Student & Face
1. Go to `http://localhost:5000/student/signup`.
2. Enter Student ID (e.g., `23CSR004`), Name, Email, Password, Department (`CSE`), Year (`4`), Section (`C`), and Phone.
3. Login as the student.
4. On the Student Dashboard, click **Register / Update Face**.
5. Allow webcam access and click **Start Face Capture**. The system automatically captures 10 face samples, extracts embeddings, and saves them to MySQL.

### B. How Staff Starts Attendance
1. Login as Staff (e.g. `CSE001` or `CSE011`, Password: `Password123` or your created credentials).
2. Go to **Staff Dashboard**.
3. View allocated classes for today. Click **START ATTENDANCE** on the current timetable hour.
4. The system starts an `ACTIVE` attendance session and opens the live camera feed.

### C. How Student Marks Attendance (Self Attendance)
1. Login as Student (e.g., `23CSR001`, Password: `Password123`).
2. Go to **Mark Attendance**.
3. The system checks if an active class session exists for the student's department, year, section, and current timetable hour.
4. Click **Mark Attendance**. The camera verifies that the recognized face matches the logged-in student ID before recording attendance as `PRESENT`.

### D. How Reports Work
1. Go to **Reports** in the navigation bar.
2. Toggle between **Consolidated Summary**, **Course Wise**, **Daily Attendance**, and **Weekly Attendance**.
3. Attendance percentages are calculated exclusively from `CLOSED` class sessions to guarantee precision.
4. Click **Download Official PDF Report** to export a printable document.

---

## 6. RUNNING AUTOMATED TESTS
Run unit and integration tests:
```bash
python -m unittest discover tests/
```

# DL_FACIAL_ATT
