from models.maintenance_activity import MaintenanceActivityModel
from db import db
from common.utils import get_metadata
from werkzeug.security import generate_password_hash
from config import MAINTAINER_WORK_HOURS, MAINTAINER_WORK_START_HOUR
from exceptions.role_error import RoleError
from exceptions.invalid_agenda_error import InvalidAgendaError
import time


class UserModel(db.Model):
    """User class for database interaction"""
    __tablename__ = "users"

    username = db.Column(db.String(128), primary_key=True)
    password = db.Column(db.String(128))
    role = db.Column(db.Enum("admin", "maintainer", "planner",
                             name="role_enum", create_type=False))

    maintenance_activities = db.relationship(
        "MaintenanceActivityModel", lazy="dynamic")

    work_hours = MAINTAINER_WORK_HOURS
    work_start_hour = MAINTAINER_WORK_START_HOUR

    def __init__(self, username, password, role):
        """UserModel constructor.

        Args:
            username (str): The user username
            password (str): The user password
            role (str): The user role (admin, maintainer or planner)
        """
        self.username = username
        self.password = generate_password_hash(password)
        self.role = role

    def json(self):
        """Public representation for user instance.
        It hides the hashed password for security concerns.

        Returns:
            dict of (str, str): The dictionary representation of user.
        """
        return {
            "username": self.username,
            "role": self.role
        }

    def save_to_db(self):
        """Saves user instance to the database"""
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        """Updates user instance with passed data.

        Args:
            data (dict of (str, str)): Dictionary of username, hashed password and role, optionals.
        """
        for k in data:
            if(data[k] and k != "password"):
                setattr(self, k, data[k])
            elif(k == "password"):
                setattr(self, "password",
                        generate_password_hash(data["password"]))

    def update_and_save(self, data):
        """Updates user instance with passed data and saves it to the database. 

        Args:
            data (dict of (str, str)): Dictionary of username, hashed password and role, optionals.
        """
        self.update(data)
        self.save_to_db()

    def delete_from_db(self):
        """Deletes user instance from database"""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        """Finds an user in the database based on given username.

        Args:
            username (str): The username of the user to retrieve.

        Returns:
            UserModel: The found user
        """
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_all(cls):
        """Finds every user in the database

        Returns:
            list of (UserModel): List of found users
        """
        return cls.query.all()

    @classmethod
    def find_some(cls, current_page=1, page_size=10):
        """Finds the selected page of users by means of given current_page and page_size.
            Fails if current_page does not exist.

        Args:
            current_page (int, optional): The desired page number, starting from 1. Defaults to 1.
            page_size (int, optional): The desired page size. Defaults to 10.

        Returns:
            ( list of (UserModel), dict of (str, int) ): 
            The first tuple element is a list of paginated UserModel instances; The second tuple element is the pagination metadata;
        """
        rows = cls.query.offset(
            page_size*(current_page-1)).limit(page_size).all()

        meta = get_metadata(
            cls.query.paginate(page=current_page, per_page=page_size)
        )
        return rows, meta

    @classmethod
    def find_all_maintainers(cls):
        return cls.query.filter_by(role="maintainer").all()

    @classmethod
    def find_some_maintainers(cls, current_page=1, page_size=10):
        rows = cls.query.filter_by(role="maintainer").offset(
            page_size*(current_page-1)).limit(page_size).all()

        meta = get_metadata(
            cls.query.filter_by(role="maintainer").paginate(
                page=current_page, per_page=page_size)
        )
        return rows, meta

    def get_daily_activities(self, week, week_day):
        if(self.role != "maintainer"):
            raise RoleError(
                "The user is not a maintaner, therefore it does not have availabilities")
        return MaintenanceActivityModel.find_all_in_day_for_user(
            self.username, week, week_day)

    class DailyAgenda:
        created_at = time.time()

        def __init__(self, user, week, week_day):
            self.user: UserModel = user
            self.week: int = week
            self.week_day: int = week_day
            activities = user.get_daily_activities(self.week, self.week_day)
            self.agenda = self._calculate_agenda_dictionary(activities)

        def json(self):
            return self.agenda

        def _calculate_agenda_dictionary(self, activities):
            d = {}

            for hour in range(self.user.work_start_hour, self.user.work_start_hour+self.user.work_hours):
                d[hour] = 60
            for activity in activities:
                d[activity.start_time] -= activity.estimated_time

            visited_hours = []
            for hour in sorted(d.keys(), reverse=True):
                if d[hour] < 0:
                    for visited_hour in reversed(visited_hours):
                        m = min(d[visited_hour], -d[hour])
                        d[visited_hour] -= m
                        d[hour] += m
                        if d[hour] >= 0:
                            break
                    if d[hour] != 0:
                        raise InvalidAgendaError()

                visited_hours.append(hour)
            return d

        def is_activity_insertable(self, activity_id, start_time):
            if start_time < self.user.work_start_hour or start_time > self.user.work_start_hour + self.user.work_hours:
                return False, "Invalid start_time"
            activity = MaintenanceActivityModel.find_by_id(activity_id)
            if not activity:
                return False, "Activity not found"

            activity.start_time = start_time
            activities = self.user.get_daily_activities(
                self.week, self.week_day)
            activities = list(
                filter(lambda a: a.activity_id != activity.activity_id, activities))
            activities.append(activity)
            try:
                self._calculate_agenda_dictionary(activities)
                return True, "Ok"
            except InvalidAgendaError as e:
                return False, e.message

    def get_daily_agenda(self, week, week_day):
        if(self.role != "maintainer"):
            raise RoleError(
                "The user is not a maintaner, therefore it does not have availabilities")
        return self.DailyAgenda(
            self, week, week_day)

    def can_do_activity(self, activity_id, week_day, start_time):
        activity = MaintenanceActivityModel.find_by_id(activity_id)
        if not activity:
            return False, "Activity not found"
        daily_agenda = self.DailyAgenda(self, activity.week, week_day)
        return daily_agenda.is_activity_insertable(activity_id, start_time)

    class DailyPercentageAvailability:
        def __init__(self, user, week, week_day):
            if(user.role != "maintainer"):
                raise RoleError(
                    "The user is not a maintaner, therefore it does not have availabilities")
            self.user: UserModel = user
            self.week = week
            self.week_day = week_day
            self.d = self._calculate_daily_percentage_availability()

        def json(self):
            return self.d

        def _calculate_daily_percentage_availability(self):
            activities = self.user.get_daily_activities(
                self.week, self.week_day)
            busy_minutes = MaintenanceActivityModel.get_total_estimated_time(
                activities)
            busy_hours = busy_minutes / 60
            return f"{ round(100 - ( 100 * busy_hours/self.user.work_hours)) }%"

    def get_daily_percentage_availability(self, week, week_day):
        return self.DailyPercentageAvailability(self, week, week_day).json()

    class WeeklyPercentageAvailability:
        _week_days = ["monday", "tuesday", "wednesday",
                      "thursday", "friday", "saturday", "sunday"]

        def __init__(self, user, week):
            if(user.role != "maintainer"):
                raise RoleError(
                    "The user is not a maintaner, therefore it does not have availabilities")
            self.user: UserModel = user
            self.week = week
            self.d = self._calculate_weekly_percentage_availability_dictionary()

        def _calculate_weekly_percentage_availability_dictionary(self):
            d = {}
            for week_day in self._week_days:
                d[week_day] = self.user.get_daily_percentage_availability(
                    self.week, week_day)
            return d

        def json(self):
            return self.d

    def get_weekly_percentage_availability(self, week):
        return self.WeeklyPercentageAvailability(
            self, week)
