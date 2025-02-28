from flask import Flask, request, jsonify
import numpy as np
import pandas as pd
import joblib
from facenet_pytorch import MTCNN, InceptionResnetV1
from scipy.spatial.distance import cosine
from domain.faceModel.neo4jConf import database
import traceback
from PIL import Image
from flask_restx import Namespace, Resource  # Using Resource for class-based views

# Initialize models
detector = MTCNN(image_size=160, margin=0)
facenet_model = InceptionResnetV1(pretrained='vggface2').eval()

# Load the fraud detection model (ensure it can process the raw input dataframe)
fraud_model = joblib.load(r'C:\Users\yousef hefny\OneDrive - Nile University\Desktop\python\FraudShield\fraud_detection_model.pkl')

api = Namespace('fusion', description='Fusion operations')

# Expected training columns for fraud detection (ensure these match what your fraud_model expects)
TRAINING_COLUMNS = [
    'step', 'type', 'amount', 'oldbalanceOrg', 'newbalanceOrig',
    'oldbalanceDest', 'newbalanceDest', 'isFlaggedFraud',
    'typing_time_normalized', 'combined_fraud'
]

def validate_transaction(transaction_data):
    """Validate transaction parameters."""
    errors = []
    if transaction_data.get('amount', 0) < 0:
        errors.append("Negative transaction amount")
    if transaction_data['type'] in ['CASH_OUT', 'TRANSFER']:
        old_balance = transaction_data.get('oldbalanceOrg', 0)
        if old_balance < transaction_data['amount']:
            errors.append("Insufficient balance for transaction")
    return errors

@api.route('/verify')
class VerifyEndpoint(Resource):
    def post(self):
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
            # Open the image using PIL and ensure it is in RGB mode
            image = Image.open(image_file).convert("RGB")
            
            # Detect and extract the face using MTCNN; returns a cropped face tensor
            face_tensor = detector(image)
            if face_tensor is None:
                return jsonify({
                    "status": "rejected",
                    "message": "No face detected",
                    "face_verified": False,
                    "fraud_probability": None
                }), 400

            # Get face embedding: add batch dimension, process, then normalize
            face_tensor = face_tensor.unsqueeze(0)
            embedding = facenet_model(face_tensor)
            embedding = embedding.detach().numpy()[0]
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
            # Prepare transaction data; no preprocessor is used now
            transaction_df = pd.DataFrame([transaction_data])[TRAINING_COLUMNS]
            fraud_prob = fraud_model.predict_proba(transaction_df)[0][1]

            # --- Decision Logic ---
            decision = "approved"
            messages = []
            if not face_verified:
                decision = "rejected"
                messages.append("Face verification failed")
            if fraud_prob > 0.7:
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
