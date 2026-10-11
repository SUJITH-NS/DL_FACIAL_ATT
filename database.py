import pymysql

from config import Config


def get_db_connection():
    """
    Establishes and returns a new MySQL connection.
    """
    return pymysql.connect(
        host=Config.DB_HOST,
        port=Config.DB_PORT,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def execute_query(sql, params=None, fetchone=False, fetchall=False):
    """
    Executes a SQL query with parameters and manages connection and cursor life-cycle.
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            if fetchone:
                return cursor.fetchone()
            if fetchall:
                return cursor.fetchall()
            return cursor.lastrowid if cursor.lastrowid > 0 else cursor.rowcount
    except Exception as e:
        print(f"[DB ERROR] Query failed: {sql} | Params: {params} | Error: {e}")
        raise e
    finally:
        if conn:
            conn.close()

# --- STUDENT DATABASE FUNCTIONS ---

def get_student_by_id(student_id):
    sql = "SELECT * FROM students WHERE student_id = %s"
    return execute_query(sql, (student_id,), fetchone=True)

def get_student_by_email(email):
    sql = "SELECT * FROM students WHERE email = %s"
    return execute_query(sql, (email,), fetchone=True)

def create_student(student_id, name, email, password_hash, department, year, section, phone):
    sql = """
    INSERT INTO students (student_id, name, email, password_hash, department, year, section, phone)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    return execute_query(sql, (student_id, name, email, password_hash, department, year, section, phone))

def get_students_by_class(department, year, section):
    sql = """
    SELECT s.student_id, s.name, s.email, s.department, s.year, s.section, s.phone,
           (SELECT COUNT(*) FROM face_embeddings fe WHERE fe.student_id = s.student_id) as face_registered
    FROM students s
    WHERE s.department = %s AND s.year = %s AND s.section = %s
    ORDER BY s.student_id ASC
    """
    return execute_query(sql, (department, year, section), fetchall=True)

# --- STAFF DATABASE FUNCTIONS ---

def get_staff_by_id(staff_id):
    sql = "SELECT * FROM staff WHERE staff_id = %s"
    return execute_query(sql, (staff_id,), fetchone=True)

def get_staff_by_email(email):
    sql = "SELECT * FROM staff WHERE email = %s"
    return execute_query(sql, (email,), fetchone=True)

def create_staff(staff_id, name, email, password_hash, department):
    sql = """
    INSERT INTO staff (staff_id, name, email, password_hash, department)
    VALUES (%s, %s, %s, %s, %s)
    """
    return execute_query(sql, (staff_id, name, email, password_hash, department))

def get_staff_allocations(staff_id, day=None):
    if day:
        sql = """
        SELECT * FROM staff_class_allocation
        WHERE staff_id = %s AND day = %s
        ORDER BY hour ASC
        """
        return execute_query(sql, (staff_id, day), fetchall=True)
    else:
        sql = """
        SELECT * FROM staff_class_allocation
        WHERE staff_id = %s
        ORDER BY FIELD(day, 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'), hour ASC
        """
        return execute_query(sql, (staff_id,), fetchall=True)

def get_allocation_by_details(staff_id, day, hour):
    sql = """
    SELECT * FROM staff_class_allocation
    WHERE staff_id = %s AND day = %s AND hour = %s
    """
    return execute_query(sql, (staff_id, day, hour), fetchone=True)

# --- FACE EMBEDDINGS FUNCTIONS ---

def save_face_embedding(student_id, embedding_json, image_path):
    sql = """
    INSERT INTO face_embeddings (student_id, embedding, image_path)
    VALUES (%s, %s, %s)
    """
    return execute_query(sql, (student_id, embedding_json, image_path))

def get_all_student_embeddings():
    sql = """
    SELECT fe.id, fe.student_id, fe.embedding, s.name, s.department, s.year, s.section
    FROM face_embeddings fe
    JOIN students s ON fe.student_id = s.student_id
    """
    return execute_query(sql, fetchall=True)

def get_embeddings_by_student(student_id):
    sql = "SELECT * FROM face_embeddings WHERE student_id = %s"
    return execute_query(sql, (student_id,), fetchall=True)

def delete_student_embeddings(student_id):
    sql = "DELETE FROM face_embeddings WHERE student_id = %s"
    return execute_query(sql, (student_id,))

# --- NOTIFICATION FUNCTIONS ---

def create_notification(student_id, message):
    sql = "INSERT INTO notifications (student_id, message) VALUES (%s, %s)"
    return execute_query(sql, (student_id, message))

def get_student_notifications(student_id, limit=20):
    sql = """
    SELECT * FROM notifications
    WHERE student_id = %s
    ORDER BY created_at DESC
    LIMIT %s
    """
    return execute_query(sql, (student_id, limit), fetchall=True)

def mark_notification_read(notification_id, student_id):
    sql = "UPDATE notifications SET is_read = TRUE WHERE id = %s AND student_id = %s"
    return execute_query(sql, (notification_id, student_id))

# --- AUDIT LOG FUNCTIONS ---

def log_audit(user_id, user_type, action):
    sql = "INSERT INTO audit_logs (user_id, user_type, action) VALUES (%s, %s, %s)"
    return execute_query(sql, (user_id, user_type, action))
