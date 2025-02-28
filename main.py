from flask import Flask, send_from_directory
from flask_restx import Api
from flask_cors import CORS
from config import Config
from flask_jwt_extended import JWTManager
from core.services.database import init_neo4j

# Import APIs

from apis.users.user_controller import api as user_ns
from domain.fusion.fusion import api as fusion_ns
# from apis.auth.auth_controller import api as auth_ns
# main.py (partial)
# from apis.auth.auth_controller import api as auth_ns

app = Flask(__name__)
CORS(app)

# Configuration
app.config.from_object(Config)
init_neo4j(app)

# JWT Setup
jwt = JWTManager(app)

# API Setup
api = Api(app, version='1.0', title='Fraud Detection API',
          description='API for Fraud Detection System', prefix='/api/v1')

# File upload route
@app.route('/upload/images/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER_IMAGES'], filename)


# api.add_namespace(transaction_ns)
# api.add_namespace(notification_ns)
api.add_namespace(user_ns, path='/users')
api.add_namespace(fusion_ns, path='/fusion')
# api.add_namespace(auth_ns, path='/auth')
# api.add_namespace(auth_ns, path='/auth')
if __name__ == '__main__':
    # Create constraints and indexes on first run
    with app.app_context():
        from core.services.schema_setup import create_constraints, create_indexes
        create_constraints()
        create_indexes()
    
    app.run(debug=True)
