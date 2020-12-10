from models.maintenance_activity import MaintenanceActivityModel
from flask_restful import Resource, reqparse


class MaintenanceActivity(Resource):
    """User API for get (single), put and delete operations."""
    _activity_parser = reqparse.RequestParser()
    _activity_parser.add_argument("activity_id",
                                  type=int,
                                  required=True,
                                  help="ID should be unique"
                                  )
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
                                  type=str,
                                  required=True,
                                  help="Interruptible should be yes or not"
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
    def get(cls, id):
        """Gets one Maintenance Activity from database based on given id. 
            Fails if there is no activity with that id.

        TODO
        """
        pass

    @classmethod
    def put(cls, id):
        pass

    @classmethod
    def delete(cls, id):
        """Deletes one activity from database based on given id. 
            Fails if there is no activty with that id.
            TODO
        """
        pass


class MaintenanceActivityCreate(Resource):
    """Maintenance Activity API for post operations."""
    _activity_parser = reqparse.RequestParser()
    _activity_parser = reqparse.RequestParser()
    _activity_parser.add_argument("activity_id",
                                  type=int,
                                  required=True,
                                  help="ID should be unique"
                                  )
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
                                  type=str,
                                  required=True,
                                  help="Interruptible should be yes or not"
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

    @ classmethod
    def post(cls):
        """Creates one Maintenance Activity in the database. 
            Fails if there is already an activity with that id.
        TODO
        Args:

        Returns:
            dict of (str, any): Jsonified activity or error message.
        """
        data = cls._activity_parser.parse_args()

        try:
            if MaintenanceActivityModel.find_by_id(data["activity_id"]):
                return {"message": "Maintenance Activity with id '{}' already exists".format(data["activity_id"])}, 400

            activity = MaintenanceActivityModel(**data)
            activity.save_to_db()
        except Exception as e:
            return {"error": str(e)}, 500

        return activity.json(), 201
