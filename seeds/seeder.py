from flask_seeder import Seeder, Faker, generator
from models.user import UserModel
from models.maintenance_activity import MaintenanceActivityModel
import random


class UserSeeder(Seeder):

    # run() will be called by Flask-Seeder
    def run(self):
        # Create a new Faker and tell it how to create User objects

        print("EMPTING DATABASE")
        self.db.drop_all()
        self.db.create_all()

        print("ADDING BASE USERS")
        user_seeds = [
            {'username': 'admin', 'password': 'password', 'role': 'admin'},
            {'username': 'planner', 'password': 'password', 'role': 'planner'},
            {'username': 'maintainer', 'password': 'password', 'role': 'maintainer'},
        ]

        for seed in user_seeds:
            user = UserModel(**seed)
            print("Adding user ", user.json())
            self.db.session.add(user)

        print("ADDING MAINTAINER USERS")
        faker = Faker(
            cls=UserModel,
            init={
                "username": generator.Name(),
                "password": "password",
                "role": "maintainer"
            }
        )

        # Create 5 more maintainers
        for user in faker.create(5):
            print("Adding user ", user.json())
            self.db.session.add(user)

        print("ADDING MAINTENANCE ACTIVITIES")
        faker = Faker(
            cls=MaintenanceActivityModel,
            init={
                'activity_type': 'planned',
                'site': generator.String("\c{10,30}"),
                'typology': generator.String("\c{10,30}"),
                'description': generator.String("\c{40,100}"),
                'estimated_time': generator.Integer(10, 100),
                'interruptible': random.choice([True, False]),
                'materials': random.choice([generator.String("\c{10,30}"), None]),
                'week': generator.Integer(1, 52),
                'workspace_notes': random.choice([generator.String("\c{40,100}"), None])
            }
        )

        # Creates 150 maintenance activities
        for activity in faker.create(150):
            print("Adding activity ", activity.json())
            self.db.session.add(activity)

        print("SEEDING COMPLETED")
