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
        """Finds every user with role 'maintainer' in the database

        Returns:
            list of (UserModel): List of found users
        """
        return cls.query.filter_by(role="maintainer").all()

    @classmethod
    def find_some_maintainers(cls, current_page=1, page_size=10):
        """Finds the selected page of users  with role 'maintainer' by means of given current_page and page_size.
            Fails if current_page does not exist.

        Args:
            current_page (int, optional): The desired page number, starting from 1. Defaults to 1.
            page_size (int, optional): The desired page size. Defaults to 10.

        Returns:
            ( list of (UserModel), dict of (str, int) ): 
            The first tuple element is a list of paginated UserModel instances; The second tuple element is the pagination metadata;
        """
        rows = cls.query.filter_by(role="maintainer").offset(
            page_size*(current_page-1)).limit(page_size).all()

        meta = get_metadata(
            cls.query.filter_by(role="maintainer").paginate(
                page=current_page, per_page=page_size)
        )
        return rows, meta

    def get_daily_activities(self, week, week_day, exclude=None):
        """Finds every activity for a user with role 'maintainer' in a given day.

        Args:
            week (int): The nth week of the year
            week_day (str): The day of the week (i.e.: monday, tuesday, ...)
            exclude (int, optional): a valid identifier for an activity that has to be assigned

        Raises:
            RoleError: If the user's role is not 'maintainer'

        Returns:
            list of (MaintenanceActivityModel): List of found Maintenance Activities
        """
        if(self.role != "maintainer"):
            raise RoleError(
                "The user is not a maintaner, therefore it does not have availabilities")
        return MaintenanceActivityModel.find_all_in_day_for_user(
            self.username, week, week_day, exclude)

    class DailyAgenda:
        """A class used to represent the daily availability for a user with role 'maintainer'

        Raises:
            RoleError: If the user's role is not 'maintainer'
            InvalidAgendaError: If the user does not have enough time to perform the maintenance activities

        Returns:
            DailyAgenda: An object with information about the user, the day associated with the agenda 
            and a dictionary with his availabilities classified by hour
        """
        _created_at = time.time()

        def __init__(self, user, week, week_day, exclude=None):
            """DailyAgenda constructor

            Args:
                user (UserModel): The user associated with the DailyAgenda
                week (int): The nth week of the year
                week_day (str): The day of the week (i.e.: monday, tuesday, ...)
                exclude (int, optional): a valid identifier for an activity that has to be assigned

            Raises:
                RoleError: If the user's role is not 'maintainer'
            """
            if(user.role != "maintainer"):
                raise RoleError(
                    "The user is not a maintaner, therefore it does not have availabilities")
            self.user: UserModel = user
            self.week: int = week
            self.week_day: int = week_day
            self.exclude = exclude
            self.agenda = self._calculate_agenda_dictionary()

        def json(self):
            """Public representation for the DailyAgenda.

            Returns:
                dict of (str, int): The dictionary representation of the agenda.
            """
            return self.agenda

        def _calculate_agenda_dictionary(self, append=None):
            """Private method used to calculate the dictionary of user's daily availabilities

            Args:
                append (MaintenanceActivityModel, optional): a MaintenanceActivityModel that has to be included in the agenda dictionary calculation

            Raises:
                InvalidAgendaError: If the user does not have enough time to perform the maintenance activities

            Returns:
                dict of (str, int): The dictionary with the work hour as key and the minutes left free for the user in that hour
            """
            activities = self.user.get_daily_activities(
                self.week, self.week_day, self.exclude)
            if append:
                activities.append(append)
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
            """Checks if a new activity can be inserted in the user's schedule given his time left in the DailyAgenda

            Args:
                activity_id (int): The id for the new activity that has to be inserted
                start_time (int): The hour that the activity has to be scheduled to

            Returns:
                (bool, str): A tuple that contains a boolean that tells if the answer is insertable, and a string
                that tells a message about the obtained response 
            """
            if start_time < self.user.work_start_hour or start_time > self.user.work_start_hour + self.user.work_hours:
                return False, "Invalid start_time"
            activity = MaintenanceActivityModel.find_by_id(activity_id)
            if not activity:
                return False, "Activity not found"

            activity.start_time = start_time
            try:
                self._calculate_agenda_dictionary(append=activity)
                return True, "Ok"
            except InvalidAgendaError as e:
                return False, e.message

    def get_daily_agenda(self, week, week_day, exclude=None):
        """Returns a DailyAgenda for the user instance

        Raises:
            RoleError: If the user's role is not 'maintainer'
            InvalidAgendaError: If the user does not have enough time to perform the maintenance activities

        Args:
                week (int): The nth week of the year
                week_day (str): The day of the week (i.e.: monday, tuesday, ...)
                exclude (int, optional): a valid identifier for an activity that has to be assigned

        Returns:
            DailyAgenda: The DailyAgenda for the user instance
        """
        return self.DailyAgenda(
            self, week, week_day, exclude)

    def can_do_activity(self, activity_id, week_day, start_time):
        """Checks if a new activity can be inserted in the user's schedule given his time left in his DailyAgenda

        Raises:
            RoleError: If the user's role is not 'maintainer'
            InvalidAgendaError: If the user does not have enough time to perform the maintenance activities

        Args:
            activity_id (int): The id for the new activity that has to be inserted
            start_time (int): The hour that the activity has to be scheduled to
            week_day (str): The day of the week (i.e.: monday, tuesday, ...)

        Returns:
            (bool, str): A tuple that contains a boolean that tells if the answer is insertable, and a string
            that tells a message about the obtained response 
        """
        activity = MaintenanceActivityModel.find_by_id(activity_id)
        if not activity:
            return False, "Activity not found"
        daily_agenda = self.DailyAgenda(
            self, activity.week, week_day, exclude=activity_id)
        return daily_agenda.is_activity_insertable(activity_id, start_time)

    class DailyPercentageAvailability:
        """A class used to represent the daily percentage availability for a user with role 'maintainer'

        Raises:
            RoleError: If the user's role is not 'maintainer'

        Returns:
            DailyPercentageAvailability: An object with information about the user, the day associated with the 
            DailyPercentageAvailability and a percentage that represents his availability for the whole day
        """

        def __init__(self, user, week, week_day, exclude=None):
            """DailyPercentageAvailability constructor

            Args:
                user (UserModel): The user associated with the DailyPercentageAvailability
                week (int): The nth week of the year
                week_day (str): The day of the week (i.e.: monday, tuesday, ...)
                exclude (int, optional): a valid identifier for an activity that has to be assigned

            Raises:
                RoleError: If the user's role is not 'maintainer'
            """
            if(user.role != "maintainer"):
                raise RoleError(
                    "The user is not a maintaner, therefore it does not have availabilities")
            self.user: UserModel = user
            self.week = week
            self.week_day = week_day
            self.exclude = exclude
            self.percentage = self._calculate_daily_percentage_availability()

        def json(self):
            """Public representation for the DailyPercentageAvailability.

            Returns:
                (str): A string representing the percentage availability for an user in a whole day.
            """
            return self.percentage

        def _calculate_daily_percentage_availability(self):
            """Private method used to calculate the user's percentage availability for a whole day

            Returns:
                (str): A string representing the percentage availability for an user in a whole day.
            """
            activities = self.user.get_daily_activities(
                self.week, self.week_day, self.exclude)
            busy_minutes = MaintenanceActivityModel.get_total_estimated_time(
                activities)
            busy_hours = busy_minutes / 60
            return f"{ round(100 - ( 100 * busy_hours/self.user.work_hours)) }%"

    def get_daily_percentage_availability(self, week, week_day, exclude=None):
        """Returns a DailyPercentageAvailability for the user instance

        Raises:
            RoleError: If the user's role is not 'maintainer'

        Args:
            week (int): The nth week of the year
            week_day (str): The day of the week (i.e.: monday, tuesday, ...)
            exclude (int, optional): a valid identifier for an activity that has to be assigned

        Returns:
            DailyAgenda: The DailyPercentageAvailability for the user instance
        """
        return self.DailyPercentageAvailability(self, week, week_day, exclude)

    class WeeklyPercentageAvailability:
        """A class used to represent the weekly percentage availability for a user with role 'maintainer'

        Raises:
            RoleError: If the user's role is not 'maintainer'

        Returns:
            WeeklyPercentageAvailability: An object with information about the user, the week associated with the 
            WeeklyPercentageAvailability and a dictionary with his percentage availabilities classified by day of the week
        """
        _week_days = ["monday", "tuesday", "wednesday",
                      "thursday", "friday", "saturday", "sunday"]

        def __init__(self, user, week, exclude=None):
            """The WeeklyPercentageAvailability constructor

            Args:
                user (UserModel): The user associated with the WeeklyPercentageAvailability
                week (int): The nth week of the year
                exclude (int, optional): a valid identifier for an activity that has to be assigned

            Raises:
                RoleError: If the user's role is not 'maintainer'
            """
            if(user.role != "maintainer"):
                raise RoleError(
                    "The user is not a maintaner, therefore it does not have availabilities")
            self.user: UserModel = user
            self.week = week
            self.exclude = exclude
            self.d = self._calculate_weekly_percentage_availability_dictionary()

        def _calculate_weekly_percentage_availability_dictionary(self):
            """Private method used to calculate the dictionary of user's weekly availabilities

            Returns:
                dict of (str, str): The dictionary with the day of the week as key and the percentage left free for the user in that day
            """
            d = {}
            for week_day in self._week_days:
                d[week_day] = self.user.get_daily_percentage_availability(
                    self.week, week_day, self.exclude).json()
            return d

        def json(self):
            """Public representation for the WeeklyPercentageAvailability.

            Returns:
                dict of (str, str): The dictionary representation of the WeeklyPercentageAvailability.
            """
            return self.d

    def get_weekly_percentage_availability(self, week, exclude=None):
        """Returns a WeeklyPercentageAvailability for the user instance

        Raises:
            RoleError: If the user's role is not 'maintainer'

        Args:
            week (int): The nth week of the year
            exclude (int, optional): a valid identifier for an activity that has to be assigned

        Returns:
            WeeklyPercentageAvailability: The WeeklyPercentageAvailability for the user instance
        """
        return self.WeeklyPercentageAvailability(
            self, week, exclude)
