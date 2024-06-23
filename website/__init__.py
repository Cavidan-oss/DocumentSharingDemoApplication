from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from flask_login import LoginManager
from dotenv import load_dotenv


def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.secret_key = os.environ.get('APP_SECRET')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE_URL")

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix = '/')
    app.register_blueprint(auth, url_prefix = '/auth/')

    from .models import User, Organization, Document, db, Archive

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    with app.app_context():
        db.create_all()

    return app