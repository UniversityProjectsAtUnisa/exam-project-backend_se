from flask_restful import Api
from flask_jwt_extended import JWTManager
from blacklist import BLACKLIST

from resources.image import Image, ImageList
from resources.category import Category, CategoryList
from resources.task import Task, TaskCreator, TaskList
from resources.achievement import Achievement, AchievementList
from resources.update import Update
from resources.user import UserRegister, UserLogin, UserLogout, User, UserList, TokenRefresh


def create_app():
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object('config.Config')
    return app


app = create_app()
api = Api(app)


@app.route("/")
def home():
    return "Hello World"


jwt = JWTManager(app)

api.add_resource(User, "/user/<int:id>")
api.add_resource(UserList, "/users")

if __name__ == "__main__":
    from db import db
    db.init_app(app)

    @app.before_first_request
    def create_tables():
        db.create_all()

    app.run()
