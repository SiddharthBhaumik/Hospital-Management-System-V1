class config:
    #python -c "import secrets; print(secrets.token_hex())" as recommended by flask

    SECRET_KEY='b5031adf39e1babfa740c485bc30b5e61cb943ac713a1275720c63354e535c3d'
    SQLALCHEMY_DATABASE_URI='sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS=False