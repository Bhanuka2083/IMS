from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager
from flask import session
from datetime import timedelta

db = SQLAlchemy()
DB_NAME = "database.db"


def creat_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "hELLOwORLD"
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix = "/")
    app.register_blueprint(auth, url_prefix = "/")



    from .models import User, Category, Product, Stock

    create_database(app) #Call to function to ctreate the database

# Create session
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))



    return app


# Create database
def create_database(app):
    if not path.exists("Project/" + DB_NAME):
        with app.app_context():
            db.create_all()
        print("--------------------Database Created Successfuly--------------------")


        