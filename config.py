import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'secret-key'

    BLOB_ACCOUNT = os.environ.get('BLOB_ACCOUNT') or 'ENTER_STORAGE_ACCOUNT_NAME'
    BLOB_STORAGE_KEY = os.environ.get('BLOB_STORAGE_KEY') or 'ENTER_BLOB_STORAGE_KEY'
    BLOB_CONTAINER = os.environ.get('BLOB_CONTAINER') or 'ENTER_IMAGES_CONTAINER_NAME'

    SQL_SERVER = os.environ.get('SQL_SERVER') or 'localhost'
    SQL_DATABASE = os.environ.get('SQL_DATABASE') or 'AricleCms'
    SQL_USER_NAME = os.environ.get('SQL_USER_NAME') or 'local'
    SQL_PASSWORD = os.environ.get('SQL_PASSWORD') or 'localpassword'
    SQLALCHEMY_DATABASE_URI = 'mssql+pyodbc://' + SQL_USER_NAME + ':' + SQL_PASSWORD + '@' + SQL_SERVER + ':1433/' + SQL_DATABASE  + '?driver=ODBC+Driver+17+for+SQL+Server'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    CLIENT_ID = os.environ.get('CLIENT_ID')
    CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
    AUTHORITY = os.environ.get('AUTHORITY')
    REDIRECT_PATH = "/getAToken"
    SCOPE = os.environ.get('SCOPE') or ["User.Read"]

    SESSION_TYPE = "filesystem" 