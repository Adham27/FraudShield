from PIL import Image
import numpy as np
from imageio import imread
from scipy.spatial.distance import cosine

def verify(account_number, image):
    results = detector.detect_faces(image)
    if not results:
        return {"embedding_id": None, "score": None, "message": "No face detected in the image."}

    # Extract the first detected face
    x, y, width, height = results[0]['box']
    face = Image.fromarray(image[y:y+height, x:x+width])

    # Create a user node
    database.create_user_if_not_exists(account_number)

    # Step 2: Generate embedding for the detected face
    face = face.resize((160, 160))  # FaceNet expects 160x160
    face_array = np.array(face)
    embedding = facenet_model.embeddings(np.expand_dims(face_array, axis=0))[0]

    # Normalize the embedding
    embedding = embedding / np.linalg.norm(embedding)

    # Step 3: Retrieve stored embeddings from the database
    stored_embeddings = database.get_embeddings(account_number)

    # Step 4: Compare the detected embedding to stored embeddings
    if stored_embeddings:
        similarity_scores = []
        for embedding_id, stored_embedding in stored_embeddings:
            stored_embedding = stored_embedding / np.linalg.norm(stored_embedding)  # Normalize stored embedding
            score = 1 - cosine(embedding, stored_embedding)
            similarity_scores.append((embedding_id, score))

        print("similarity_scores", similarity_scores)

        # Find the best match
        best_match = max(similarity_scores, key=lambda x: x[1])
        embedding_id, max_score = best_match

        if max_score > 0.65:  # Increased threshold
            database.update_embedding(embedding_id, embedding, isFraud=0)
            return {"embedding_id": embedding_id, "score": max_score, "message": "Face verified. Embedding updated."}
        else:
            embedding_id = database.store_embedding(account_number, embedding, isFraud=1)
            return {"embedding_id": None, "score": max_score, "message": "Face does not match. No updates made."}
    else:
        # If no embeddings are stored, create a new embedding node
        embedding_id = database.store_embedding(account_number, embedding, isFraud=1)
        return {"embedding_id": embedding_id, "score": None, "message": "No stored embeddings found. New embedding stored."}