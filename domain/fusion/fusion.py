from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import joblib
# from mtcnn import MTCNN
from keras_facenet import FaceNet
from scipy.spatial.distance import cosine
from domain.faceModel.neo4jConf import database
import traceback
from PIL import Image
from flask_restx import Namespace  # Assuming you're using flask_restx for Namespace

# Initialize models and preprocessor
# detector = MTCNN()
facenet_model = FaceNet()
fraud_model = joblib.load('/home/user/backend/fraud_detection_model.pkl')
preprocessor = joblib.load('preprocessor.pkl')  # Load your saved preprocessor

api = Namespace('fusion', description='Fusion operations')

# Load expected column order (replace with your actual training columns)
TRAINING_COLUMNS = [
    'step', 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig',
    'oldbalanceDest', 'newbalanceDest', 'isFlaggedFraud',
    'typing_time_normalized', 'combined_fraud'
]

def validate_transaction(transaction_data):
    """Validate transaction parameters"""
    errors = []
    
    # Check for negative amount
    if transaction_data.get('amount', 0) < 0:
        errors.append("Negative transaction amount")
    
    # Check sufficient balance for relevant transaction types
    if transaction_data['type'] in ['CASH_OUT', 'TRANSFER']:
        old_balance = transaction_data.get('oldbalanceOrg', 0)
        if old_balance < transaction_data['amount']:
            errors.append("Insufficient balance for transaction")
    
    return errors

@api.route('/verify', methods=['POST'])
def verify_endpoint():
    try:
        # Get input data
        account_number = request.form['account_number']
        image_file = request.files['image']
        transaction_data = request.form.to_dict()
        
        # Convert numeric fields
        for field in ['step', 'amount', 'oldbalanceOrg', 'newbalanceOrig',
                      'oldbalanceDest', 'newbalanceDest', 'isFlaggedFraud',
                      'combined_fraud']:
            transaction_data[field] = float(transaction_data[field])
        
        # Validate transaction parameters
        validation_errors = validate_transaction(transaction_data)
        if validation_errors:
            return jsonify({
                "status": "rejected",
                "errors": validation_errors,
                "message": "Transaction validation failed"
            }), 400

        # --- Face Verification ---
        # Open the image using PIL directly from the file stream
        image = Image.open(image_file)
        image = np.array(image)

        # Detect face using MTCNN
        # results = detector.detect_faces(image)
        # if not results:
        #     return jsonify({
        #         "status": "rejected",
        #         "message": "No face detected",
        #         "face_verified": False,
        #         "fraud_probability": None
        #     }), 400

        # Extract and process face
        x, y, w, h = results[0]['box']
        face = Image.fromarray(image[y:y+h, x:x+w])
        face = face.resize((160, 160))  # FaceNet expects 160x160
        face_array = np.array(face)
        embedding = facenet_model.embeddings(np.expand_dims(face_array, axis=0))[0]
        embedding /= np.linalg.norm(embedding)

        # Compare with stored embeddings
        stored_embeddings = database.get_embeddings(account_number)
        face_verified = False
        max_score = 0

        if stored_embeddings:
            similarity_scores = []
            for emb_id, stored_emb in stored_embeddings:
                stored_emb = stored_emb / np.linalg.norm(stored_emb)
                score = 1 - cosine(embedding, stored_emb)
                similarity_scores.append((emb_id, score))
            
            if similarity_scores:
                best_match = max(similarity_scores, key=lambda x: x[1])
                max_score = best_match[1]
                face_verified = max_score > 0.65

        # --- Fraud Detection ---
        # Prepare transaction data
        transaction_df = pd.DataFrame([transaction_data])[TRAINING_COLUMNS]
        transaction_processed = preprocessor.transform(transaction_df)
        fraud_prob = fraud_model.predict_proba(transaction_processed)[0][1]

        # --- Decision Logic ---
        decision = "approved"
        messages = []
        
        if not face_verified:
            decision = "rejected"
            messages.append("Face verification failed")
        
        if fraud_prob > 0.7:  # Adjust threshold as needed
            decision = "rejected"
            messages.append(f"High fraud probability ({fraud_prob:.2f})")

        # Update database based on results
        if face_verified and stored_embeddings:
            database.update_embedding(best_match[0], embedding, isFraud=0)
        else:
            database.store_embedding(account_number, embedding, isFraud=1)

        return jsonify({
            "status": decision,
            "face_verified": face_verified,
            "face_match_score": max_score,
            "fraud_probability": float(fraud_prob),
            "message": ", ".join(messages) if messages else "Verification successful"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "trace": traceback.format_exc()
        }), 500
