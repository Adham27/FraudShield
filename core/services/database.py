from neomodel import config
from decouple import config as env_config
from neo4j import GraphDatabase 
def init_neo4j(app):
    config.DATABASE_URL = app.config['NEO4J_URI']
    config.AUTO_INSTALL_LABELS = True  # Automatically creates indexes/constraints
    config.ENCRYPTED_CONNECTION = True
    config.FORCE_TIMEZONE = True  

driver = GraphDatabase.driver(env_config('NEO4J_URI'), auth=(env_config('NEO4J_USER'), env_config('NEO4J_PASSWORD')))

def get_driver():
    global driver
    if driver is None:
        driver = GraphDatabase.driver(env_config('NEO4J_URI'), auth=(env_config('NEO4J_USER'), env_config('NEO4J_PASSWORD')))
    return driver