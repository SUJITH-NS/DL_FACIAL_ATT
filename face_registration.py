import os
import json
import cv2

from config import Config
from database import save_face_embedding, delete_student_embeddings, log_audit, get_student_by_id
from face_detector import validate_face_quality
from recognition import generate_face_embedding


def register_student_face_samples(student_id, image_frames, replace_existing=True):
    """
    Registers a student's facial profile by processing a batch of captured webcam images.
    
    Parameters:
    - student_id: String ID of the student
    - image_frames: List of OpenCV BGR images (10-20 samples)
    - replace_existing: If True, clears prior embeddings before storing new set.
    
    Returns: (success: bool, message: str, samples_registered: int)
    """
    student = get_student_by_id(student_id)
    if not student:
        return False, "Student record not found.", 0

    if not image_frames or len(image_frames) == 0:
        return False, "No image samples provided for facial registration.", 0

    student_img_dir = os.path.join(Config.STUDENT_IMAGES_DIR, str(student_id))
    os.makedirs(student_img_dir, exist_ok=True)

    if replace_existing:
        delete_student_embeddings(student_id)

    valid_samples_count = 0

    for idx, img in enumerate(image_frames):
        # Validate face quality
        is_valid, msg, bbox, cropped_face = validate_face_quality(img)
        if not is_valid:
            print(f"[FACE REGISTRATION SKIP] Frame {idx+1}: {msg}")
            continue

        # Extract 1280-d embedding
        embedding_vec = generate_face_embedding(cropped_face)
        if embedding_vec is None:
            continue

        # Save sample image to disk
        img_filename = f"sample_{idx+1}.jpg"
        img_path = os.path.join(student_img_dir, img_filename)
        cv2.imwrite(img_path, img)

        # Convert embedding list to JSON string for MySQL storage
        embedding_json = json.dumps(embedding_vec)

        # Store record in MySQL
        rel_path = f"images/students/{student_id}/{img_filename}"
        save_face_embedding(student_id, embedding_json, rel_path)
        valid_samples_count += 1

    if valid_samples_count == 0:
        return False, "Failed to register face: No valid face samples met quality thresholds.", 0

    log_audit(student_id, 'STUDENT', f"Registered {valid_samples_count} facial embeddings")
    return True, f"Successfully registered {valid_samples_count} facial samples for student {student['name']}.", valid_samples_count
