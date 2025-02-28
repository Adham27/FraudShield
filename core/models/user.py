from neomodel import (
    StructuredNode,
    StringProperty,
    DateTimeProperty,
    RelationshipTo,
    UniqueIdProperty,
    IntegerProperty
)
from datetime import datetime
import uuid
class User(StructuredNode):
    uid = StringProperty(default=lambda: str(uuid.uuid4()), unique_index=True)
    username = StringProperty(unique_index=True)
    email = StringProperty(unique_index=True)
    password = StringProperty()
    phone_number = StringProperty(unique_index=True)
    address = StringProperty()
    account_number=StringProperty(unique_index=True)
    profile_picture = StringProperty()
    balance=IntegerProperty(default=0)
    fcm_token=StringProperty()
    g_authId=StringProperty()
    created_at = DateTimeProperty(default=datetime.utcnow)
    updated_at = DateTimeProperty(default=datetime.utcnow)
    deleated_at = DateTimeProperty(default=datetime.utcnow)

    # Relationships
    transactions = RelationshipTo('Transaction', 'SENT')
    # frequent_recipients = RelationshipTo('User', 'FREQUENT_RECIPIENT', model='FrequentRecipient')
    #biometric = RelationshipTo('FaceModel', 'HAS_BIOMETRIC')

# class FrequentRecipient:
#     count = IntegerProperty(default=1)
#     last_transaction = DateTimeProperty()