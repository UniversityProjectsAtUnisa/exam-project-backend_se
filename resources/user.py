from models.user import UserModel
from flask_restful import Resource, reqparse
from werkzeug.security import generate_password_hash


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
    def post(cls):
        """Creates one user in the database. 
            Fails if there is alrady an user with that username.

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

            user = UserModel(
                data["username"],
                generate_password_hash(data["password"], "sha256"),
                data["role"]
            )
            user.save_to_db()
        except Exception as e:
            return {"error": str(e)}, 500

        return user.json(), 201
