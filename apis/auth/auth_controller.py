# apis/auth/auth_controller.py

from flask import request
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import create_access_token, jwt_required
import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from core.models.user import User

# Create a Namespace for auth operations.
api = Namespace('auth', description='Authentication operations using Firebase OAuth')

# Initialize Firebase Admin SDK if not already initialized.
# Replace the path with your Firebase service account JSON file.
if not firebase_admin._apps:
    cred = credentials.Certificate('C:\Users\yousef hefny\OneDrive - Nile University\Desktop\python\FraudShield\google-services.json')
    firebase_admin.initialize_app(cred)

# Models for expected input.
login_model = api.model('Login', {
    'id_token': fields.String(required=True, description='Firebase ID token')
})

register_model = api.model('Register', {
    'id_token': fields.String(required=True, description='Firebase ID token for registration')
})

@api.route('/login')
class FirebaseLogin(Resource):
    @api.expect(login_model)
    def post(self):
        """
        Accepts a Firebase ID token, verifies it with Firebase, then retrieves or creates a local user.
        Returns a JWT token and user details.
        """
        data = request.get_json()
        id_token = data.get('id_token')
        try:
            # Verify the provided Firebase ID token.
            decoded_token = firebase_auth.verify_id_token(id_token)
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            username = decoded_token.get('name') or (email.split('@')[0] if email else 'anonymous')
            
            # Look for an existing user by email.
            user = User.nodes.get_or_none(email=email)
            if not user:
                # Create a new user record if one does not exist.
                user = User(
                    username=username,
                    email=email,
                    g_authId=firebase_uid  # Store the Firebase UID for reference.
                ).save()

            # Create a JWT token that includes additional claims from Firebase.
            additional_claims = {'firebase_uid': firebase_uid, 'email': email}
            access_token = create_access_token(identity=user.uid, additional_claims=additional_claims)

            return {
                'access_token': access_token,
                'user': {
                    'uid': user.uid,
                    'username': user.username,
                    'email': user.email
                }
            }, 200

        except Exception as e:
            # Abort with a 401 error if token verification fails.
            api.abort(401, f'Invalid Firebase token: {str(e)}')

@api.route('/register')
class FirebaseRegister(Resource):
    @api.expect(register_model)
    def post(self):
        """
        Registers a new user using Firebase authentication.
        This endpoint is similar to the login endpoint but ensures that a new account is created.
        """
        data = request.get_json()
        id_token = data.get('id_token')
        try:
            decoded_token = firebase_auth.verify_id_token(id_token)
            firebase_uid = decoded_token.get('uid')
            email = decoded_token.get('email')
            username = decoded_token.get('name') or (email.split('@')[0] if email else 'anonymous')
            
            # Check if the user already exists.
            user = User.nodes.get_or_none(email=email)
            if user:
                return {'msg': 'User already registered.'}, 400
            
            # Create new user record.
            user = User(
                username=username,
                email=email,
                g_authId=firebase_uid
            ).save()
            
            # Create JWT token.
            additional_claims = {'firebase_uid': firebase_uid, 'email': email}
            access_token = create_access_token(identity=user.uid, additional_claims=additional_claims)
            
            return {
                'access_token': access_token,
                'user': {
                    'uid': user.uid,
                    'username': user.username,
                    'email': user.email
                }
            }, 201
        except Exception as e:
            api.abort(400, f'Error during registration: {str(e)}')

@api.route('/logout')
class FirebaseLogout(Resource):
    @jwt_required()
    def post(self):
        """
        Logout endpoint.
        With JWT-based authentication, logout is typically managed client-side by discarding the token.
        For more secure implementations, consider maintaining a token revocation list.
        """
        # If token revocation is desired, implement logic to blacklist the current token here.
        return {'msg': 'Logged out successfully.'}, 200
