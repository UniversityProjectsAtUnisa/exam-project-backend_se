from flask_jwt_extended.utils import get_jwt_identity
from models.user import UserModel
from flask_restful import Resource, reqparse
from werkzeug.security import check_password_hash
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_raw_jwt
)
from jwt_utils import role_required
from blacklist import BLACKLIST


class User(Resource):
    """User API for get (single), put and delete operations."""
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
    @role_required()
    def get(cls, username):
        """Gets one user from database based on given username. 
            Fails if there is no user with that username.

        Args:
            username (str): The username of the user to be retrieved.

        Returns:
            dict of (str, any): Jsonified user or error message.
        """
        try:
            user = UserModel.find_by_username(username)
        except Exception as e:
            return {"error": str(e)}, 500

        if not user:
            return {"message": "User not found"}, 404
        return user.json(), 200

    @classmethod
    @role_required()
    def put(cls, username):
        """Edits one user in the database based on given username. 
            Fails if there is no user with that username.
            Fails if there is already an user with the new username.

        Args:
            username (str): The username of the user to be edited.
            username (str, optional): Body param indicating the new username.
            role (str, optional): Body param indicating the new role.

        Returns:
            dict of (str, any): Jsonified user or error message.
        """
        data = cls._user_parser.parse_args()
        try:
            user = UserModel.find_by_username(username)

            if not user:
                return {"message": "User not found"}, 404

            if "username" in data and username != data["username"] and UserModel.find_by_username(data["username"]):
                return {"message": "User with username '{}' already exists".format(data["username"])}, 400

            user.update_and_save(data)
        except Exception as e:
            return {"error": str(e)}, 500
        return user.json(), 200

    @classmethod
    @role_required()
    def delete(cls, username):
        """Deletes one user from database based on given username. 
            Fails if there is no user with that username.

        Args:
            username (str): The username of the user to be deleted.

        Returns:
            dict of (str, any): Confirmation or error message.
        """
        try:
            user = UserModel.find_by_username(username)
            if not user:
                return {"message": "User not found"}, 404
            user.delete_from_db()

        except Exception as e:
            return {"error": str(e)}, 500

        return {"message": "User deleted"}, 200


class UserList(Resource):
    """User API for get (multiple) operations."""
    _user_parser = reqparse.RequestParser()
    _user_parser.add_argument("current_page",
                              type=int,
                              default=1
                              )
    _user_parser.add_argument("page_size",
                              type=int,
                              default=10
                              )

    @classmethod
    @role_required()
    def get(cls):
        """Gets a paginated list of users, along with its metadata. Takes current_page and page_size as optional body arguments.

        Args:
            current_page (int, optional): Body param indicating the requested page. Defaults to 1.
            page_size (int, optional): Body param indicating the page size. Defaults to 10.

        Returns:
            dict of (str, any): Json of rows and meta. Rows is the list of paginated users; meta is its metadata;
        """
        data = cls._user_parser.parse_args()
        rows, meta = UserModel.find_some(**data)
        return {"rows": [user.json() for user in rows], "meta": meta}, 200


class UserCreate(Resource):
    """User API for post operations."""
    _user_parser = reqparse.RequestParser()
    _user_parser.add_argument("username",
                              type=str, required=True,
                              help="Username should be non-empty string"
                              )
    _user_parser.add_argument("password",
                              type=str, required=True,
                              help="Password should be non-empty string"
                              )
    _user_parser.add_argument("role",
                              type=str, required=True,
                              help="Role should be admin, maintainer or planner"
                              )

    @ classmethod
    @role_required()
    def post(cls):
        """Creates one user in the database. 
            Fails if there is already an user with that username.

        Args:
            username (str): Body param indicating the new username.
            password (str): Body param indicating the new username.
            role (str): Body param indicating the new role.

        Returns:
            dict of (str, any): Jsonified user or error message.
        """
        data = cls._user_parser.parse_args()

        try:
            if UserModel.find_by_username(data["username"]):
                return {"message": "User with username '{}' already exists".format(data["username"])}, 400

            user = UserModel(**data)
            user.save_to_db()
        except Exception as e:
            return {"error": str(e)}, 500

        return user.json(), 201


class UserLogin(Resource):
    """User API for login operation."""
    _user_parser = reqparse.RequestParser()
    _user_parser.add_argument("username",
                              type=str, required=True,
                              help="Username should be non-empty string"
                              )
    _user_parser.add_argument("password",
                              type=str, required=True,
                              help="Password should be non-empty string"
                              )

    @classmethod
    def post(cls):
        """Creates an access token and a refresh token for the user with given username and password.
            Fails if there is no user with that username.
            Fails if password don't match.

        Args:
            username (str): Body param indicating the username.
            password (str): Body param indicating the password.

        Returns:
            dict of (str, str): Access token
        """
        data = cls._user_parser.parse_args()

        try:
            user = UserModel.find_by_username(data['username'])
        except Exception as e:
            return {"error": str(e)}, 500

        if not user:
            return {"message": "User not found"}, 404

        if not check_password_hash(user.password, data["password"]):
            return {"message": "Incorrect password"}, 401  # Not authorized

        access_token = create_access_token(
            identity=user.username, user_claims=user.json())
        return {"access_token": access_token}, 200


class UserLogout(Resource):
    """User API for logout operation"""
    @classmethod
    @jwt_required
    def post(cls):
        """Retrieves the current jwt id and saves it in memory, since a jwt token cannot be forced to expire.

        Returns:
            dict of (str, str): A confirmation message
        """
        # jti is "JWT ID", a unique identifier for JWT
        jti = get_raw_jwt()['jti']
        BLACKLIST.add(jti)
        return {"message": "Successfully logged out"}, 200


class UserChangePassword(Resource):
    """User API for change password operation"""
    _user_parser = reqparse.RequestParser()
    _user_parser.add_argument("old_password",
                              type=str,
                              required=True
                              )
    _user_parser.add_argument("new_password",
                              type=str,
                              required=True
                              )

    @classmethod
    @jwt_required
    def post(cls):
        """Changes the password for current user with new_password. Fails if old_password does not match the current user's stored password.

        Args:
            old_password (str): Body param indicating the old password for current user.
            new_password (str): Body param indicating the new password for current user.

        Returns:
            dict of (str, str): A confirmation message
        """

        data = cls._user_parser.parse_args()

        username = get_jwt_identity()
        try:
            user = UserModel.find_by_username(username)
        except Exception as e:
            return {"error": str(e)}, 500

        if not user:
            return {"message": "User not found"}, 404

        if not check_password_hash(user.password, data["old_password"]):
            return {"message": "Incorrect password"}, 401  # Not authorized

        try:
            user.update_and_save(dict(password=data["new_password"]))
        except Exception as e:
            return {"error": str(e)}, 500

        return {"message": "Password changed succesfully"}, 200
