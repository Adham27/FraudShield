from neomodel import StructuredNode, StringProperty, DateTimeProperty, RelationshipFrom
from datetime import datetime

class FaceModel(StructuredNode):
    template = StringProperty(required=True)  # Store biometric template
    created_at = DateTimeProperty(default=datetime.utcnow)
    user = RelationshipFrom('User', 'HAS_BIOMETRIC')