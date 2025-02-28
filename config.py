# config.py:
from decouple import config

class Config:
    SECRET_KEY = config('SECRET_KEY')
    NEO4J_URI = config('NEO4J_URI')
    NEO4J_USER = config('NEO4J_USER')
    NEO4J_PASSWORD = config('NEO4J_PASSWORD')
    UPLOAD_FOLDER_IMAGES = '/home/user/backend/public/upload'
    JWT_SECRET_KEY = config('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = 3600  
