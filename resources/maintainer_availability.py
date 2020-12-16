from flask_restful import Resource, reqparse
from jwt_utils import role_required
from models.user import UserModel
from models.maintenance_activity import MaintenanceActivityModel


class MaintainerWeeklyAvailabilityList(Resource):
    """MaintainerAvailability API to get the maintainer's weekly availabilities"""
    _activity_parser = reqparse.RequestParser()
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
    def get(cls, activity_id):
        """Gets a paginated list of Maintainers weekly availability, along with its metadata.
        For every user it returns aswell the user itself, the user's skill compliance (expressed as a fraction) 
        with the next activity that the planner wants to assign and the week in which the
        activity has to be assigned

        Args:
            activity_id (int): The identifier of the maintenance activity to be assigned.
            current_page (int, optional): Body param indicating the requested page. Defaults to 1.
            page_size (int, optional): Body param indicating the page size. Defaults to 10.

        Returns:
            dict of (str, any): Json of rows and meta or an error message. Rows is the list of paginated users' informations; meta is its metadata.
        """

        activity = MaintenanceActivityModel.find_by_id(activity_id)
        if not activity:
            return {"message": "Activity not found"}, 404

        data = cls._activity_parser.parse_args()
        rows, meta = UserModel.find_some_maintainers(**data)

        return {"rows": [
            {"user": user.json(),
                "skill_compliance": "3/5",
                "weekly_percentage_availability": user.get_weekly_percentage_availability(activity.week).json(),
                "week": activity.week
             } for user in rows
        ], "meta": meta}, 200


class MaintainerDailyAvailability(Resource):
    """MaintainerAvailability API to get the maintainer's daily availabilities"""
    _activity_parser = reqparse.RequestParser()
    _activity_parser.add_argument("activity_id",
                                  type=int,
                                  required=True,
                                  help="A valid activity_id for the activity that the planner wants to assign"
                                  )
    _activity_parser.add_argument("week_day",
                                  type=str,
                                  required=True,
                                  help="Week should be a valid weekday name (i.e: monday, tuesday, ...)"
                                  )

    @classmethod
    @role_required("planner")
    def get(cls, username):
        """Gets the public representation of the DailyAgenda for a user with given username based on the week associated with
        the activity with given activity_id and the given week_day.
        Fails if the user's role is not 'maintainer'

        Args:
            username (str): A valid username
            activity_id (int): Body param indicating the identifier of the maintenance activity to be assigned.
            week_day (str): Body param indicating the day of the week (i.e.: monday, tuesday, ...)


        Returns:
            dict of (str, any): Json representing the user's availabilities in minutes classified by hour or an error message.
        """
        agenda = None
        try:
            user: UserModel = UserModel.find_by_username(username)
            if not user:
                return {"message": "User not found"}, 404

            if user.role != "maintainer":
                return {"message": "User role for user with given username is not 'maintainer'"}, 400

            data = cls._activity_parser.parse_args()
            activity = MaintenanceActivityModel.find_by_id(data["activity_id"])
            if not activity:
                return {"message": "Activity not found"}, 404

            agenda = user.get_daily_agenda(activity.week, data["week_day"])
        except Exception as e:
            return {"error": str(e)}, 500

        return agenda.json(), 200
