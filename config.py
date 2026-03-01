import os
from urllib.parse import quote_plus

class Config:
    SECRET_KEY = os.urandom(24)
    # URL encode the password to handle special characters like '@'
    password = quote_plus('MySQLkaur@003')
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://root:{password}@localhost/journeyverse_auth'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
