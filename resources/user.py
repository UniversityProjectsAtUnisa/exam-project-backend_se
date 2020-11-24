from models.user import UserModel
from flask_restful import Resource, reqparse
from werkzeug.security import generate_password_hash, check_password_hash


class User(Resource):
    @classmethod
    def get(cls, id):
        user = UserModel.find_by_id(id)
        if not user:
            return {"message": "User not found"}, 404
        return user.json(), 201

    @classmethod
    def delete(cls, id):
        user = UserModel.find_by_id(id)
        if not user:
            return {"message": "User not found"}, 404

        user.delete_from_db()
        return {"message": "User deleted"}, 200


_user_parser = reqparse.RequestParser()
_user_parser.add_argument("username",
                          type=str, required=True,
                          help="Username should be non-empty string"
                          )


class UserList(Resource):
    @classmethod
    def get(cls):
        return [user.json() for user in UserModel.find_all()]
