from neomodel import (
    StructuredNode,
    DateTimeProperty,
    FloatProperty,
    RelationshipFrom,
    RelationshipTo,
    UniqueIdProperty,
    IntegerProperty
)
from datetime import datetime

class Transaction(StructuredNode):
    uid = UniqueIdProperty()
    amount = FloatProperty()
    fraud_score = FloatProperty()
    timestamp = DateTimeProperty(default=datetime.utcnow)
    # Relationships
    sender = RelationshipFrom('User', 'SENT')
    recipient = RelationshipTo('User', 'RECEIVED_BY')
