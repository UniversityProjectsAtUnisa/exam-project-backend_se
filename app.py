from flask_restful import Api
from resources.user import User, UserList, UserCreate


def create_app(config_class="config.Config"):
    from flask import Flask
    app = Flask(__name__)
    app.config.from_object(config_class)
    api = Api(app)

    @app.route("/")
    def home():
        return "Hello World"

    api.add_resource(User, "/user/<string:username>")
    api.add_resource(UserCreate, "/user")
    api.add_resource(UserList, "/users")
    return app


if __name__ == "__main__":
    app = create_app('config.Config')
    from db import db
    db.init_app(app)

    @app.before_first_request
    def create_tables():
        db.create_all()

    app.run()
