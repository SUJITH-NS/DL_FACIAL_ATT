import cv2
import numpy as np

from config import Config

# Initialize Cascade Classifier
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
face_cascade = cv2.CascadeClassifier(CASCADE_PATH)

# Try initializing MTCNN as secondary/high-precision detector if available
mtcnn_detector = None
try:
    from mtcnn import MTCNN
    mtcnn_detector = MTCNN()
except Exception as e:
    print(f"[FACE DETECTOR INFO] MTCNN fallback not active ({e}). Using OpenCV Cascade Classifier.")

def detect_faces(img):
    """
    Detects face bounding boxes in an OpenCV BGR image frame.
    Returns list of tuples (x, y, w, h).
    """
    if img is None:
        return []

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Scale factor 1.1, minNeighbors 5, minSize (80, 80)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=Config.MIN_FACE_SIZE,
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    if len(faces) == 0 and mtcnn_detector is not None:
        try:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = mtcnn_detector.detect_faces(rgb)
            faces = []
            for res in results:
                if res.get('confidence', 0) > 0.85:
                    box = res['box']
                    x, y, w, h = box[0], box[1], box[2], box[3]
                    faces.append((max(0, x), max(0, y), max(1, w), max(1, h)))
        except Exception as e:
            print(f"[MTCNN DETECTION ERROR] {e}")

    return faces

def validate_face_quality(img):
    """
    Validates facial quality, ensuring:
    - Image is present
    - Image is not extremely dark
    - Exactly ONE face is present
    - Face bounding box meets minimum dimensions
    
    Returns tuple: (is_valid, message, bbox, cropped_face)
    """
    if img is None or img.size == 0:
        return False, "Invalid or empty image frame received.", None, None

    # Check illumination / brightness
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    mean_brightness = np.mean(gray)
    if mean_brightness < 30:
        return False, "Image is extremely dark. Please ensure sufficient lighting.", None, None

    faces = detect_faces(img)

    if len(faces) == 0:
        return False, "No face detected in camera frame. Please center your face.", None, None

    if len(faces) > 1:
        return False, f"Multiple faces detected ({len(faces)}). Please ensure only one person is in frame.", None, None

    (x, y, w, h) = faces[0]
    min_w, min_h = Config.MIN_FACE_SIZE

    if w < min_w or h < min_h:
        return False, f"Face is too small ({w}x{h}px). Please move closer to the camera.", None, None

    # Crop face chip with small padding
    h_img, w_img = img.shape[:2]
    pad_x = int(w * 0.1)
    pad_y = int(h * 0.1)

    x1 = max(0, x - pad_x)
    y1 = max(0, y - pad_y)
    x2 = min(w_img, x + w + pad_x)
    y2 = min(h_img, y + h + pad_y)

    cropped_face = img[y1:y2, x1:x2]

    return True, "Face validated successfully.", (x, y, w, h), cropped_face
