from db import db


class UserModel(db.Model):
    __tablename__ = "users"

    username = db.Column(db.String(128), primary_key=True)
    password = db.Column(db.String(128))
    role = db.Column(db.Enum("admin", "maintainer", "planner",
                             name="role_enum", create_type=False))

    def __init__(self, username, password, role):
        self.username = username
        self.password = password
        self.role = role

    def json(self):
        return {
            "username": self.username,
            "role": self.role
        }

    def save_to_db(self):
        db.session.add(self)
        db.session.commit()

    def update(self, data):
        for k in data:
            if(data[k]):
                setattr(self, k, data[k])

    def update_and_save(self, data):
        self.update(data)
        self.save_to_db()

    def delete_from_db(self):
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def find_by_username(cls, username):
        return cls.query.filter_by(username=username).first()

    @classmethod
    def find_all(cls):
        return cls.query.all()

    # TODO: Handle pagination object
    @classmethod
    def find_some(cls, current_page=1, page_size=3):
        # return cls.query.paginate(page=current_page, per_page=page_size, max_per_page=25)

        return cls.query.offset(page_size*(current_page-1)).limit(page_size).all()
