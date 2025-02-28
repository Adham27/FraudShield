from neomodel import install_all_labels
from core.models.user import User
from core.models.transaction import Transaction, Geolocation
from core.models.face_model import FaceModel

def create_constraints():
    # Create unique constraints
    User.install_labels()
    Transaction.install_labels()
    Geolocation.install_labels()
    FaceModel.install_labels()

def create_indexes():
    # Create indexes (example)
    User.uid.create_index()
    Transaction.uid.create_index()