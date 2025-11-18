import os
from dotenv import load_dotenv

load_dotenv()

class config:
    #python -c "import secrets; print(secrets.token_hex())" as recommended by flask

    SECRET_KEY=os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI='sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS=False