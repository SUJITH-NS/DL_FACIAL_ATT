import json
import cv2
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config import Config
from database import get_all_student_embeddings
from face_detector import validate_face_quality

# Lazy initialization of Keras feature model for fast startup
_feature_model = None

def get_feature_extractor():
    global _feature_model
    if _feature_model is None:
        try:
            import tensorflow as tf
            # Suppress verbose TF logging
            tf.get_logger().setLevel('ERROR')
            _feature_model = tf.keras.applications.MobileNetV2(
                input_shape=(128, 128, 3),
                include_top=False,
                weights='imagenet',
                pooling='avg'
            )
            print("[RECOGNITION INFO] MobileNetV2 Feature Extractor initialized.")
        except Exception as e:
            print(f"[RECOGNITION WARN] Could not load MobileNetV2: {e}. Using OpenCV spatial features.")
            _feature_model = False

    return _feature_model

def generate_face_embedding(cropped_face):
    """
    Extracts a normalized 1280-d (or spatial composite) embedding vector from a cropped face image.
    Returns: list of floats (serializable to JSON).
    """
    if cropped_face is None or cropped_face.size == 0:
        return None

    # Resize image to 128x128
    face_resized = cv2.resize(cropped_face, (128, 128))
    
    extractor = get_feature_extractor()
    if extractor:
        # Convert BGR to RGB and scale to [-1, 1] for MobileNetV2
        rgb_img = cv2.cvtColor(face_resized, cv2.COLOR_BGR2RGB)
        input_arr = np.expand_dims(rgb_img.astype(np.float32) / 127.5 - 1.0, axis=0)
        feat_vector = extractor(input_arr, training=False).numpy()[0]
    else:
        # Fallback multi-scale spatial histogram feature vector
        gray = cv2.cvtColor(face_resized, cv2.COLOR_BGR2GRAY)
        hist = cv2.calcHist([gray], [0], None, [256], [0, 256]).flatten()
        resized_flat = cv2.resize(gray, (32, 32)).flatten()
        feat_vector = np.concatenate([hist, resized_flat])

    # L2 Normalization
    norm = np.linalg.norm(feat_vector)
    if norm > 0:
        feat_vector = feat_vector / norm

    return feat_vector.tolist()

def compute_similarity(embedding_a, embedding_b):
    """
    Calculates cosine similarity between two embedding vectors using scikit-learn.
    Returns float between -1.0 and 1.0.
    """
    vec_a = np.array(embedding_a, dtype=np.float32).reshape(1, -1)
    vec_b = np.array(embedding_b, dtype=np.float32).reshape(1, -1)
    
    sim = cosine_similarity(vec_a, vec_b)[0][0]
    return float(sim)

def recognize_face(frame_or_face, threshold=None):
    """
    Performs end-to-end face recognition against all registered student embeddings in MySQL.
    
    Returns dict:
    {
        "matched": bool,
        "student_id": str or None,
        "name": str,
        "confidence": float (0-100),
        "department": str,
        "year": int,
        "section": str,
        "message": str
    }
    """
    if threshold is None:
        threshold = Config.RECOGNITION_THRESHOLD

    # Validate face quality & detect face chip
    is_valid, msg, bbox, cropped_face = validate_face_quality(frame_or_face)
    if not is_valid:
        return {
            "matched": False,
            "student_id": None,
            "name": "Unknown",
            "confidence": 0.0,
            "message": msg
        }

    # Generate embedding vector
    input_embedding = generate_face_embedding(cropped_face)
    if input_embedding is None:
        return {
            "matched": False,
            "student_id": None,
            "name": "Unknown",
            "confidence": 0.0,
            "message": "Failed to generate facial embedding."
        }

    # Fetch all stored embeddings from MySQL database
    stored_records = get_all_student_embeddings()
    if not stored_records:
        return {
            "matched": False,
            "student_id": None,
            "name": "Unknown",
            "confidence": 0.0,
            "message": "No registered face embeddings found in database."
        }

    best_match = None
    highest_similarity = -1.0

    # Map candidate similarities per student
    student_sims = {}

    for record in stored_records:
        student_id = record['student_id']
        try:
            stored_emb = json.loads(record['embedding'])
            sim = compute_similarity(input_embedding, stored_emb)
            
            if student_id not in student_sims:
                student_sims[student_id] = {
                    "record": record,
                    "sims": []
                }
            student_sims[student_id]["sims"].append(sim)
        except Exception as e:
            print(f"[RECOGNITION EMBEDDING ERROR] Student {student_id}: {e}")

    # Evaluate best matching student based on top 3 average similarity
    for student_id, data in student_sims.items():
        sims = sorted(data["sims"], reverse=True)
        top_avg = np.mean(sims[:3]) if len(sims) >= 3 else np.mean(sims)
        
        if top_avg > highest_similarity:
            highest_similarity = top_avg
            best_match = data["record"]

    confidence_pct = round(highest_similarity * 100, 2)

    if highest_similarity >= threshold and best_match:
        return {
            "matched": True,
            "student_id": best_match['student_id'],
            "name": best_match['name'],
            "confidence": confidence_pct,
            "department": best_match['department'],
            "year": best_match['year'],
            "section": best_match['section'],
            "message": f"Successfully recognized as {best_match['name']} ({confidence_pct}% confidence)."
        }
    else:
        return {
            "matched": False,
            "student_id": None,
            "name": "Unknown",
            "confidence": max(0.0, confidence_pct),
            "message": "Face not recognized. Similarity below threshold."
        }
