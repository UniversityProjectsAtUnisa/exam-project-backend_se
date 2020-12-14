from db import db
from common.utils import get_metadata


class MaintenanceActivityModel(db.Model):
    """Maintenance Activity class for database interaction"""
    __tablename__ = "maintenance activity"

    activity_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    activity_type = db.Column(db.Enum("planned", "unplanned", "extra",
                                      name="type_enum", create_type=False))
    site = db.Column(db.String(128))
    typology = db.Column(db.String(128))
    description = db.Column(db.String(128))
    estimated_time = db.Column(db.Integer)
    interruptible = db.Column(db.Enum("yes", "no",
                                      name="interruptible_enum", create_type=False))
    materials = db.Column(db.String(128), nullable=True)
    week = db.Column(db.Integer, db.CheckConstraint(
        "week >= 1 AND week <= 52"))
    workspace_notes = db.Column(db.String(128), nullable=True)

    def __init__(self, activity_type, site, typology, description, estimated_time,
                 interruptible, week, materials=None, workspace_notes=None, activity_id=None):
        """ 
        MaintenanceActivityModel constructor.

        Args:
            activity_id (int): Unique identifier for Maintenance Activities
            activity_type(String): Type of the Activity
            site(String): Factory's site and area in which the Activity will be performed
            typology(String): Typology of the Activity
            description(String): Description of the Activity
            estimated_time(int): Expected Activity's lifetime in minutes
            interruptible(String): Is the Activity interruptible by a Emergency Work Order?
            materials(String): List of materials to be used during the Activity
            week(int): Week (1 to 52) in which the activity will be performed
            workspace_notes(String): Editable description of the workspace
        """
        self.activity_id = activity_id
        self.activity_type = activity_type
        self.site = site
        self.typology = typology
        self.description = description
        self.estimated_time = estimated_time
        self.interruptible = interruptible
        self.materials = materials
        self.week = week
        self.workspace_notes = workspace_notes

    def json(self):
        """Public representation for MaintenanceActivityModel instance.
        Returns:
            dict of (str, str): The dictionary representation of Maintenance Activity.
        """
        return {
            "activity_id": self.activity_id,
            "activity_type": self.activity_type,
            "site": self.site,
            "typology": self.typology,
            "description": self.description,
            "estimated_time": self.estimated_time,
            "interruptible": self.interruptible,
            "materials": self.materials,
            "week": self.week,
            "workspace_notes": self.workspace_notes
        }

    def save_to_db(self):
        """Saves user instance to the database"""
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        """Updates activity's workspace notes with passed data.
        Args:
            data (dict of (str, str)): Dictionary of activity's attributes.
        """
        for k in data:
            if(data[k] and k == "workspace_notes"):
                setattr(self, k, data[k])

    def update_and_save(self, data):
        """Updates MaintenanceActivityModel instance with passed data and saves it to the database. 

        Args:
            data (dict of (str, str)): Dictionary of activity's attributes.
        """
        self.update(data)
        self.save_to_db()

    def delete_from_db(self):
        """Deletes MaintenanceActivityModel instance from database"""
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_id(cls, activity_id):
        """Finds a Maintenance Activity in the database based on given id.
        Args:
            activity_id (int): The identifier of the Maintenance Activity to retrieve.
        Returns:
            MaintenanceActivityModel: The found activity
        """
        return cls.query.filter_by(activity_id=activity_id).first()

    @classmethod
    def find_all(cls):
        """Finds every Maintenance Activity in the database
        Returns:
            list of (MaintenanceActivityModel): List of found Maintenance Activities
        """
        return cls.query.all()

    @classmethod
    def find_some(cls, current_page=1, page_size=10):
        """Finds the selected page of Maintenance Activitis by means of given current_page and page_size.
            Fails if current_page does not exist.

        Args:
            current_page (int, optional): The desired page number, starting from 1. Defaults to 1.
            page_size (int, optional): The desired page size. Defaults to 10.

        Returns:
            ( list of (MaintenanceActivityModel), dict of (str, int) ): 
            The first tuple element is a list of paginated MaintenanceActivityModel instances; 
            The second tuple element is the pagination metadata;
            """
        rows = cls.query.offset(
            page_size*(current_page-1)).limit(page_size).all()

        meta = get_metadata(
            cls.query.paginate(page=current_page, per_page=page_size)
        )
        return rows, meta
