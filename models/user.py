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

