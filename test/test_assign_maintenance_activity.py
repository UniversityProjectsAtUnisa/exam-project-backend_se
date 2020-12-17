import pytest
import config
from models.maintenance_activity import MaintenanceActivityModel


@pytest.fixture
def user_seeds():
    """Gets a list of users of type planner and maintainer

    Returns:
        list of (dict of (str, str)): The list of users
    """
    return [
        {'username': 'planner', 'password': 'password', 'role': 'planner'},
        {'username': 'maintainer', 'password': 'password', 'role': 'maintainer'},
        {'username': 'maintainer1', 'password': 'password', 'role': 'maintainer'},
        {'username': 'maintainer2', 'password': 'password', 'role': 'maintainer'},
    ]


@pytest.fixture
def activity_seed():
    """Gets an activity with a preset activity_id

    Returns:
        dict of (str, any): the activity
    """
    return {'activity_id': "101", 'activity_type': 'extra', 'site': 'management',
            'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
            'interruptible': True, 'materials': 'spikes', 'week': '20',
            'workspace_notes': 'Site: Management; Typology: Electrical'}


@pytest.fixture
def activity_seed_without_id():
    """Gets an activity without a preset activity_id

    Returns:
        dict of (str, any): the activity without id
    """
    return {'activity_type': 'extra', 'site': 'management',
            'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
            'interruptible': True, 'materials': 'spikes', 'week': '20',
            'workspace_notes': 'Site: Management; Typology: Electrical'}


@pytest.fixture
def planner_user(user_seeds):
    """ Finds the first planner user among the user seeds

    Returns:
        dict of (str, str): The planner user
    """
    return next(user for user in user_seeds if user["role"] == "planner")


@pytest.fixture
def maintainer_user(user_seeds):
    """ Finds the first maintainer user among the user seeds

    Returns:
        dict of (str, str): The maintainer user
    """
    return next(user for user in user_seeds if user["role"] == "maintainer")


@pytest.fixture(autouse=True)
def setup(app, user_seeds):
    """Before each test it drops every table and recreates them.
    Then it creates an user for every dictionary present in user_seeds

    Returns:
        boolean: the return status
    """
    with app.app_context():
        from db import db
        db.drop_all()
        db.create_all()
        from models.user import UserModel
        for seed in user_seeds:
            user = UserModel(**seed)
            user.save_to_db()
    return True


@pytest.fixture
def planner_client(client, planner_user):
    """ Creates a test client with preset planner authorization headers taken from the login endpoint 

    Returns:
        FlaskClient: The test client
    """
    res = client.post(
        "/login", data=planner_user)
    access_token = res.get_json()["access_token"]
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + access_token
    return client


def test_no_activities_success(app, planner_client, activity_seed, maintainer_user):
    """ Tests a successful activity assignment to a maintainer when there is no maintenance activity stored in the database """
    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "maintainer_username": maintainer_user["username"], "week_day": "monday", "start_time": config.MAINTAINER_WORK_START_HOUR}

    res = planner_client.put(
        f"/activity/{activity_seed['activity_id']}/assign", data=data)

    assert res.status_code == 200
    assert "message" in res.get_json().keys()
    assert res.get_json()["message"] == "Activity assigned successfully"


def test_some_activities_success(app, planner_client, activity_seed, activity_seed_without_id, maintainer_user):
    """ Tests a successful activity assignment to a maintainer who is already associated to some activities """
    with app.app_context():
        start_time = config.MAINTAINER_WORK_START_HOUR
        end_time = start_time + config.MAINTAINER_WORK_HOURS
        # Create many assigned activities and assign them to a maintainer without filling his work schedule
        while start_time < end_time - 1:
            activity = MaintenanceActivityModel(**activity_seed_without_id)
            activity.maintainer_username = maintainer_user["username"]
            activity.week_day = "monday"
            activity.start_time = start_time
            activity.save_to_db()
            start_time += 1
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "maintainer_username": maintainer_user["username"], "week_day": "monday", "start_time": start_time}

    res = planner_client.put(
        f"/activity/{activity_seed['activity_id']}/assign", data=data)

    assert res.status_code == 200
    assert "message" in res.get_json().keys()
    assert res.get_json()["message"] == "Activity assigned successfully"


def test_maintainer_full_schedule(app, planner_client, activity_seed, activity_seed_without_id, maintainer_user):
    """ Tests a failed activity assignment to a maintainer who already has a full schedule """
    with app.app_context():
        start_time = config.MAINTAINER_WORK_START_HOUR
        end_time = start_time + config.MAINTAINER_WORK_HOURS
        # Create many assigned activities and assign them to a maintainer in order to fill his work schedule
        i = start_time
        while i < end_time:
            activity = MaintenanceActivityModel(**activity_seed_without_id)
            activity.maintainer_username = maintainer_user["username"]
            activity.week_day = "monday"
            activity.start_time = i
            activity.save_to_db()
            i += 1
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "maintainer_username": maintainer_user["username"], "week_day": "monday", "start_time": start_time}

    res = planner_client.put(
        f"/activity/{activity_seed['activity_id']}/assign", data=data)

    assert res.status_code == 400
    assert "message" in res.get_json().keys()


def test_wrong_user_role(app, planner_client, planner_user, activity_seed):
    """ Test a failed activity assignment to an user whose role is not 'maintainer' """

    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "maintainer_username": planner_user["username"], "week_day": "monday", "start_time": 8}
    res = planner_client.put(
        f"/activity/{activity_seed['activity_id']}/assign", data=data)

    assert res.status_code == 400
    assert "message" in res.get_json()


def test_user_not_found(app, planner_client, activity_seed):
    """ Test a failed activity assignment to an user that does not exist """
    unexisting_user_id = 0

    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "maintainer_username": unexisting_user_id, "week_day": "monday", "start_time": 8}
    res = planner_client.put(
        f"/activity/{activity_seed['activity_id']}/assign", data=data)

    assert res.status_code == 404
    assert "message" in res.get_json()


def test_activity_not_found(app, planner_client, maintainer_user, activity_seed):
    """ Test a failed activity assignment of an activity that does not exist """
    unexisting_activity_id = 0

    data = {
        "maintainer_username": maintainer_user["username"], "week_day": "monday", "start_time": 8}
    res = planner_client.put(
        f"/activity/{unexisting_activity_id}/assign", data=data)

    assert res.status_code == 404
    assert "message" in res.get_json()
