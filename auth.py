from functools import wraps
from flask import session, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database import get_student_by_id, get_student_by_email, get_staff_by_id, get_staff_by_email, create_student, create_staff, log_audit
from utils import format_json_response, validate_email


def hash_password(password):
    return generate_password_hash(password)

def verify_password(stored_hash, password):
    return check_password_hash(stored_hash, password)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or 'role' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return format_json_response(False, "Authentication required. Please login.", status_code=401)
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'STUDENT':
            if request.is_json or request.path.startswith('/api/'):
                return format_json_response(False, "Unauthorized: Student access required.", status_code=403)
            flash("Unauthorized access. Student portal only.", "danger")
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def staff_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'STAFF':
            if request.is_json or request.path.startswith('/api/'):
                return format_json_response(False, "Unauthorized: Staff access required.", status_code=403)
            flash("Unauthorized access. Staff portal only.", "danger")
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def authenticate_user(user_id_or_email, password, role):
    """
    Authenticates user credentials against the specified role.
    """
    user = None
    if role == 'STUDENT':
        user = get_student_by_id(user_id_or_email) or get_student_by_email(user_id_or_email)
    elif role == 'STAFF':
        user = get_staff_by_id(user_id_or_email) or get_staff_by_email(user_id_or_email)

    if not user:
        return False, "User not found with provided ID or email."

    user_password_hash = user['password_hash']
    if not verify_password(user_password_hash, password):
        return False, "Invalid password. Please try again."

    user_id = user['student_id'] if role == 'STUDENT' else user['staff_id']
    
    # Store session variables
    session['user_id'] = user_id
    session['role'] = role
    session['user_name'] = user['name']
    session['email'] = user['email']
    session['department'] = user['department']
    if role == 'STUDENT':
        session['year'] = user['year']
        session['section'] = user['section']

    log_audit(user_id, role, f"User logged in successfully")
    return True, "Login successful."

def register_student_account(student_id, name, email, password, department, year, section, phone):
    """
    Registers a new student account with validation.
    """
    if not student_id or not name or not email or not password or not department:
        return False, "All required fields must be provided."

    if not validate_email(email):
        return False, "Invalid email address format."

    if get_student_by_id(student_id):
        return False, "Student ID already registered."

    if get_student_by_email(email):
        return False, "Email address already registered."

    pwd_hash = hash_password(password)
    create_student(student_id, name, email, pwd_hash, department, year, section, phone)
    log_audit(student_id, 'STUDENT', "Student registered account")
    return True, "Student registered successfully. Please login."

def register_staff_account(staff_id, name, email, password, department):
    """
    Registers a new staff account with validation.
    """
    if not staff_id or not name or not email or not password or not department:
        return False, "All required fields must be provided."

    if not validate_email(email):
        return False, "Invalid email address format."

    if get_staff_by_id(staff_id):
        return False, "Staff ID already registered."

    if get_staff_by_email(email):
        return False, "Email address already registered."

    pwd_hash = hash_password(password)
    create_staff(staff_id, name, email, pwd_hash, department)
    log_audit(staff_id, 'STAFF', "Staff registered account")
    return True, "Staff registered successfully. Please login."
