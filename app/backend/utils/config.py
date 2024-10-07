import os

class Config:
    DEBUG = os.getenv("DEBUG", False)
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
    CORS_ALLOW_ORIGIN = os.getenv("CORS_ALLOW_ORIGIN", "*")
    AUTH_USER_MODEL = 'users'
