# apis/user_controller.py

from flask_restx import Namespace, Resource, fields
import uuid
import datetime
from core.services.database import driver  # our Neo4j driver instance

api = Namespace('users', description='User operations')

# Define the user model for Swagger documentation
user_model = api.model('User', {
    'uid':fields.String(required=False, description='User id'),
    'name': fields.String(required=True, description='User name'),
    "email": fields.String(required=True, description='User email'),
    "password": fields.String(required=True, description='User password'),
    "phone_number": fields.String(required=True, description='User phone number'),
    "address": fields.String(required=True, description='User address'),
    'biometric_hash': fields.String(required=True, description='Biometric hash'),
    'account_number': fields.String(required=True, description='Account number'),
    'profile_picture': fields.String(required=True, description='Profile picture'),
    'fcm_token': fields.String(required=True, description='FCM token'),
    'g_authId':fields.String(required=False, description='Google authentication ID'),
    'created_at':fields.String(required=False, description='Created at'),
    'updated_at':fields.String(required=False, description='Updated at')
})

@api.route('/')
class UserList(Resource):
    @api.doc('list_users')
    def get(self):
        """List all users"""
        query = "MATCH (u:User) RETURN u"
        with driver.session() as session:
            result = session.run(query)
            users = []
            for record in result:
                u = record['u']
                users.append({
                    'id': u.get('uid'),
                    'name': u.get('username'),
                    'email': u.get('email'),
                    'phone_number' : u.get('phone_number'),
                    'address' : u.get('address'),
                    'account_number':u.get('account_number'),
                    'profile_picture' :u.get('profile_picture'),
                    'fcm_token':u.get('fcm_token'),
                    'g_authId':u.get('g_authId'),
                    'biometric_hash': u.get('biometric_hash'),
                    'created_at': u.get('created_at')
                })
            return users, 200

    @api.doc('create_user')
    @api.expect(user_model)
    def post(self):
        """Create a new user"""
        data = api.payload
        data['created_at'] = datetime.datetime.utcnow().isoformat()
        query = """
            CREATE (u:User {name: $username, biometric_hash: $biometric_hash,
            account_number: $account_number, address: $address,phone_number:$phone_number,fcm_token:$fcm_token, 
            created_at: $created_at })
            RETURN u
        """
        with driver.session() as session:
            result = session.run(query, **data)
            record = result.single()
            if record:
                return {'message': 'User created', 'user': data}, 201
            return {'message': 'User creation failed'}, 500

@api.route('/<string:user_id>')
@api.param('user_id', 'The user identifier')
class User(Resource):
    @api.doc('get_user')
    def get(self, user_id):
        """Fetch a user given its identifier"""
        query = "MATCH (u:User {id: $user_id}) RETURN u"
        with driver.session() as session:
            result = session.run(query, user_id=user_id)
            record = result.single()
            if record:
                u = record['u']
                return {
                   'id': u.get('id'),
                    'name': u.get('username'),
                    'email': u.get('email'),
                    'phone_number' : u.get('phone_number'),
                    'address' : u.get('address'),
                    'account_number':u.get('account_number'),
                    'profile_picture' :u.get('profile_picture'),
                    'fcm_token':u.get('fcm_token'),
                    'g_authId':u.get('g_authId'),
                    'biometric_hash': u.get('biometric_hash'),
                    'created_at': u.get('created_at')
                }, 200
            api.abort(404, f"User {user_id} doesn't exist")

    @api.doc('update_user')
    @api.expect(user_model)
    def put(self, user_id):
        """Update a user given its identifier"""
        data = api.payload
        query = """
            MATCH (u:User {id: $user_id})
            SET u.name = $name, u.biometric_hash = $biometric_hash,
                u.latitude = $latitude, u.longitude = $longitude
            RETURN u
        """
        with driver.session() as session:
            result = session.run(query, user_id=user_id, **data)
            record = result.single()
            if record:
                u = record['u']
                return {
                    'id': u.get('id'),
                    'name': u.get('name'),
                    'biometric_hash': u.get('biometric_hash'),
                    'created_at': u.get('created_at')
                }, 200
            api.abort(404, f"User {user_id} doesn't exist")

    @api.doc('delete_user')
    def delete(self, user_id):
        """Delete a user given its identifier"""
        query = "MATCH (u:User {id: $user_id}) DETACH DELETE u RETURN COUNT(u) as deleted_count"
        with driver.session() as session:
            result = session.run(query, user_id=user_id)
            record = result.single()
            if record and record['deleted_count'] > 0:
                return {'message': 'User deleted'}, 200
            api.abort(404, f"User {user_id} doesn't exist")
