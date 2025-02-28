from neo4j import GraphDatabase

class Neo4jDatabase:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        """Close the Neo4j driver."""
        self.driver.close()

    def get_embeddings(self, user_id):
        """
        Retrieve all embeddings for a given user.
        Returns a list of tuples (embedding_id, embedding).
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MATCH (u:User {user_id: $user_id})-[:HAS_FACE]->(f:FaceEmbedding)
                RETURN f.embedding_id AS embedding_id, f.embedding AS embedding
                """,
                user_id=user_id
            )
            return [(record["embedding_id"], np.array(record["embedding"])) for record in result]

    def create_user_if_not_exists(self, user_id):
        """
        Create a User node with user_id if it does not already exist.
        Returns the user_id.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                MERGE (u:User {user_id: $user_id})
                RETURN u.user_id AS user_id
                """,
                user_id=user_id
            )

            record = result.single()

            if record:
                print(f"User created or already exists: {record['user_id']}")
                return record["user_id"]
            else:
                print(f"Failed to create or find user with user_id: {user_id}")
                return None



    def store_embedding(self, user_id, embedding, isFraud=0):
        """
        Store a new embedding for a user.
        Returns the embedding_id of the newly created node.
        """
        with self.driver.session() as session:
            result = session.run(
                """
                CREATE (f:FaceEmbedding {embedding_id: randomUUID(), embedding: $embedding, isFraud: $isFraud})
                WITH f
                MATCH (u:User {user_id: $user_id})
                MERGE (u)-[:HAS_FACE]->(f)
                RETURN f.embedding_id AS embedding_id
                """,
                embedding=embedding.tolist(),
                user_id=user_id,
                isFraud=isFraud,
            )
            print("result.single", result)
            return result.single()["embedding_id"]

    def update_embedding(self, embedding_id, embedding, isFraud=0):
        """
        Update an existing embedding.
        """
        with self.driver.session() as session:
            session.run(
                """
                MATCH (f:FaceEmbedding {embedding_id: $embedding_id})
                SET f.embedding = $embedding, f.isFraud = $isFraud
                """,
                embedding_id=embedding_id,
                isFraud=isFraud,
                embedding=embedding.tolist()
            )

# Initialize the database layer
database = Neo4jDatabase("neo4j+s://51a677e3.databases.neo4j.io", "neo4j", "A-J48XoEs3J8m4XrEbHXrTF4aBrpBwlm-Qla41iXEtU")