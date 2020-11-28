from models.user import UserModel
from flask_restful import Resource, reqparse
from werkzeug.security import generate_password_hash, check_password_hash


class User(Resource):
    _user_parser = reqparse.RequestParser()
    _user_parser.add_argument("username",
                              type=str,
                              required=False,
                              help="Username should be non-empty string"
                              )
    _user_parser.add_argument("role",
                              type=str,
                              required=False,
                              help="Role should be admin, maintainer or planner"
                              )

    @classmethod
    def get(cls, username):
        try:
            user = UserModel.find_by_username(username)
        except Exception as e:
            return {"error": str(e)}, 500

        if not user:
            return {"message": "User not found"}, 404
        return user.json(), 200

    @classmethod
    def put(cls, username):
        data = cls._user_parser.parse_args()
        try:
            user = UserModel.find_by_username(username)

            if not user:
                return {"message": "User not found"}, 404

            user.update_and_save(data)
        except Exception as e:
            return {"error": str(e)}, 500
        return user.json(), 200

    @classmethod
    def delete(cls, username):
        try:
            user = UserModel.find_by_username(username)
            if not user:
                return {"message": "User not found"}, 404
            user.delete_from_db()

        except Exception as e:
            return {"error": str(e)}, 500

        return {"message": "User deleted"}, 200


class UserList(Resource):
    _user_parser = reqparse.RequestParser()
    _user_parser.add_argument("current_page",
                              type=int,
                              )
    _user_parser.add_argument("page_size",
                              type=int,
                              )

    @classmethod
    def get(cls):
        data = cls._user_parser.parse_args()
        return [user.json() for user in UserModel.find_some(**data))], 200
        # return [user.json() for user in UserModel.find_some()], 200


class UserCreate(Resource):
    _user_parser=reqparse.RequestParser()
    _user_parser.add_argument("username",
                              type = str, required = True,
                              help = "Username should be non-empty string"
                              )
    _user_parser.add_argument("password",
                              type = str, required = True,
                              help = "Password should be non-empty string"
                              )
    _user_parser.add_argument("role",
                              type = str, required = True,
                              help = "Role should be admin, maintainer or planner"
                              )

    @ classmethod
    def post(cls):
        data=cls._user_parser.parse_args()

        try:
            if UserModel.find_by_username(data["username"]):
                return {"message": "User with username '{}' already exists".format(data["username"])}, 400

            user=UserModel(
                data["username"],
                generate_password_hash(data["password"], "sha256"),
                data["role"]
            )
            user.save_to_db()
        except Exception as e:
            return {"error": str(e)}, 500

        return user.json(), 201
