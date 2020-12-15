from flask_restful import Resource, reqparse
from jwt_utils import role_required
from models.user import UserModel


class MaintainerWeeklyAvailabilityList(Resource):
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
    def get(cls, week):
        if week <= 0 or week > 52:
            raise ValueError("week's value should be between 1 and 52")

        data = cls._activity_parser.parse_args()
        rows, meta = UserModel.find_some_maintainers(**data)

        return {"rows": [
            {"user": user.json(),
             "skill_compliance": "3/5",
             "weekly_percentage_availability": user.get_weekly_percentage_availability(week).json(),
             "week": week
             } for user in rows
        ], "meta": meta}, 200


class MaintainerDailyAvailability(Resource):
    _activity_parser = reqparse.RequestParser()
    _activity_parser.add_argument("week",
                                  type=int,
                                  required=True,
                                  help="Week should be an integer between 1 and 52"
                                  )
    _activity_parser.add_argument("week_day",
                                  type=str,
                                  required=True,
                                  help="Week should be a valid weekday name (i.e: monday, tuesday, ...)"
                                  )

    @classmethod
    @role_required("planner")
    def get(cls, username):
        data = cls._activity_parser.parse_args()
        agenda = None
        try:
            user: UserModel = UserModel.find_by_username(username)
            if not user:
                return {"message": "User not found"}, 404

            if user.role != "maintainer":
                return {"message": "User role for user with given username is not 'maintainer'"}, 400

            data = cls._activity_parser.parse_args()
            agenda = user.get_daily_agenda(**data)
        except Exception as e:
            return {"error": str(e)}, 500

        return agenda.json(), 200
