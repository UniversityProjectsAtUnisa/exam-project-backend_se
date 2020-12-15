from config import MAINTAINER_WORK_HOURS, MAINTAINER_WORK_START_HOUR
from models.maintenance_activity import MaintenanceActivityModel
from models.user import UserModel
from flask_restful import Resource, reqparse
from jwt_utils import role_required


class MaintenanceActivity(Resource):
    """User API for get (single), put and delete operations."""
    _activity_parser = reqparse.RequestParser()
    _activity_parser.add_argument("workspace_notes",
                                  type=str,
                                  required=False,
                                  help="Workspace Notes should be a short description of the workspace"
                                  )

    @classmethod
    @role_required("planner")
    def get(cls, id):
        """Gets one activity from database based on given id.
            Fails if there is no activity with that id.

        Args:
            id (int): The identifier of the maintenance activity to be retrieved.

        Returns:
            dict of (str, any): Jsonified activity or error message.
        """
        try:
            activity = MaintenanceActivityModel.find_by_id(id)
        except Exception as e:
            return {"error": str(e)}, 500

        if not activity:
            return {"message": "Activity not found"}, 404
        return activity.json(), 200

    @classmethod
    @role_required("planner")
    def put(cls, id):
        """Edits one activity in the database based on given id.
            Fails if there is no activity with that id.

        Args:
            id (int): The identifier of the activity to be edited.
            workspace_notes (str): Body param indicating the new workspace notes.

        Returns:
            dict of (str, any): Jsonified activity or error message.
        """
        data = cls._activity_parser.parse_args()
        try:
            activity = MaintenanceActivityModel.find_by_id(id)

            if not activity:
                return {"message": "Activity not found"}, 404

            activity.update_and_save(data)
        except Exception as e:
            return {"error": str(e)}, 500
        return activity.json(), 200

    @classmethod
    @role_required("planner")
    def delete(cls, id):
        """Deletes one activity from database based on given id.
            Fails if there is no activity with that id.

        Args:
            id (int): The identifier of the activity to be deleted.

        Returns:
            dict of (str, any): Confirmation or error message.
        """
        try:
            activity = MaintenanceActivityModel.find_by_id(id)
            if not activity:
                return {"message": "Activity not found"}, 404
            activity.delete_from_db()

        except Exception as e:
            return {"error": str(e)}, 500

        return {"message": "Activity deleted"}, 200


class MaintenanceActivityList(Resource):
    """Maintenance Activity API for get (multiple) operations."""
    _activity_parser = reqparse.RequestParser()
    _activity_parser.add_argument("week",
                                  type=int,
                                  required=False
                                  )
    _activity_parser.add_argument("current_page",
                                  type=int,
                                  default=1
                                  )
    _activity_parser.add_argument("page_size",
                                  type=int,
                                  default=10
                                  )

    @classmethod
    @role_required("planner")
    def get(cls):
        """Gets a paginated list of activites, along with its metadata. Takes current_page and page_size as optional body arguments.

        Args:
            current_page (int, optional): Body param indicating the requested page. Defaults to 1.
            page_size (int, optional): Body param indicating the page size. Defaults to 10.

        Returns:
            dict of (str, any): Json of rows and meta. Rows is the list of paginated activities; meta is its metadata;
        """
        data = cls._activity_parser.parse_args()
        rows, meta = [], {}
        try:
            if data["week"]:
                rows, meta = MaintenanceActivityModel.find_some_in_week(
                    **data)
            else:
                rows, meta = MaintenanceActivityModel.find_some(
                    data["current_page"], data["page_size"])
        except Exception as e:
            return {"error": str(e)}, 500

        return {"rows": [activity.json() for activity in rows], "meta": meta}, 200


class MaintenanceActivityCreate(Resource):
    """Maintenance Activity API for post operations."""
    _activity_parser = reqparse.RequestParser()
    _activity_parser.add_argument("activity_type",
                                  type=str,
                                  required=True,
                                  help="Type should be planned, unplanned or extra"
                                  )
    _activity_parser.add_argument("site",
                                  type=str,
                                  required=True,
                                  help="Site should be a factory's location"
                                  )
    _activity_parser.add_argument("typology",
                                  type=str,
                                  required=True,
                                  help="Typology should be the context of the Maintenance Activity"
                                  )
    _activity_parser.add_argument("description",
                                  type=str,
                                  required=True,
                                  help="Description of the activity"
                                  )
    _activity_parser.add_argument("estimated_time",
                                  type=int,
                                  required=True,
                                  help="Estimated Time should be the expected duration of the activty, in minutes"
                                  )
    _activity_parser.add_argument("interruptible",
                                  type=bool,
                                  required=True,
                                  help="Interruptible should be True (yes) or False (not)"
                                  )
    _activity_parser.add_argument("materials",
                                  type=str,
                                  required=False,
                                  help="Materials should be the list of materials needed for the activity"
                                  )
    _activity_parser.add_argument("week",
                                  type=int,
                                  required=True,
                                  help="Week should be an integer between 1 and 52"
                                  )
    _activity_parser.add_argument("workspace_notes",
                                  type=str,
                                  required=False,
                                  help="Workspace Notes should be a short description of the workspace"
                                  )

    @classmethod
    @role_required("planner")
    def post(cls):
        """Creates one activity in the database.

        Returns:
            dict of (str, any): Jsonified activity or error message.
        """
        data = cls._activity_parser.parse_args()

        try:
            activity = MaintenanceActivityModel(**data)
            activity.save_to_db()
        except Exception as e:
            return {"error": str(e)}, 500

        return activity.json(), 201


class MaintenanceActivityAssign(Resource):
    _activity_parser = reqparse.RequestParser()
    _activity_parser.add_argument("maintainer_username",
                                  type=str,
                                  required=True,
                                  help="maintainer_username should be a valid maintainer username"
                                  )
    _activity_parser.add_argument("week_day",
                                  type=str,
                                  required=True,
                                  help="Week should be a valid weekday name (i.e: monday, tuesday, ...)"
                                  )
    _activity_parser.add_argument("start_time",
                                  type=int,
                                  required=True,
                                  help=f"start_time should be an integer between {MAINTAINER_WORK_START_HOUR} and {MAINTAINER_WORK_START_HOUR + MAINTAINER_WORK_HOURS}"
                                  )

    @classmethod
    @role_required("planner")
    def put(cls, id):
        data = cls._activity_parser.parse_args()

        try:
            activity = MaintenanceActivityModel.find_by_id(id)
            if not activity:
                return {"message": "Activity not found"}, 404

            user = UserModel.find_by_username(data["maintainer_username"])
            if not user:
                return {"message": "User not found"}, 404

            if user.role != "maintainer":
                return {"message": "User role for user with given username is not 'maintainer'"}, 400

            is_doable, reason = user.can_do_activity(
                id, data["week_day"], data["start_time"])
            if not is_doable:
                return {"message": reason}

            activity.update_and_save(data)

        except Exception as e:
            return {"error": str(e)}, 500

        return {"message": "Activity assigned successfully"}, 200
