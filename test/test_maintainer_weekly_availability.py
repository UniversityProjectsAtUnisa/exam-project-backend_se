from test.test_maintenance_activity import unexisting_activity
import pytest
import config
from models.maintenance_activity import MaintenanceActivityModel
import math


@pytest.fixture
def user_seeds():
    """Gets a list of users for every possible role with multiple maintainers

    Returns:
        list of (dict of (str, str)): list of users
    """
    return [
        {'username': 'admin', 'password': 'password', 'role': 'admin'},
        {'username': 'planner', 'password': 'password', 'role': 'planner'},
        {'username': 'maintainer', 'password': 'password', 'role': 'maintainer'},
        {'username': 'maintainer1', 'password': 'password', 'role': 'maintainer'},
        {'username': 'maintainer2', 'password': 'password', 'role': 'maintainer'},
    ]


@pytest.fixture
def activity_seed():
    """Gets an activity

    Returns:
        dict of (str, any): the activity
    """
    return {'activity_id': "101", 'activity_type': 'extra', 'site': 'management',
            'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
            'interruptible': True, 'materials': 'spikes', 'week': '20',
            'workspace_notes': 'Site: Management; Typology: Electrical'}


@pytest.fixture
def activity_seed_without_id():
    """Gets an activity that does not have an activity_id

    Returns:
        dict of (str, any): the activity without id
    """
    return {'activity_type': 'extra', 'site': 'management',
            'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
            'interruptible': True, 'materials': 'spikes', 'week': '20',
            'workspace_notes': 'Site: Management; Typology: Electrical'}


@pytest.fixture
def admin_user(user_seeds):
    """ Finds the first admin user among the user seeds

    Returns:
        dict of (str, str): The admin user
    """
    return next(user for user in user_seeds if user["role"] == "admin")


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


@pytest.fixture
def maintainer_users(user_seeds):
    """ Finds the maintainer users among the user seeds

    Returns:
        list of (dict of (str, str)): List of maintainer users
    """
    return [user for user in user_seeds if user["role"] == "maintainer"]


@pytest.fixture
def week_days():
    """ Returns the list of the day of the week

    Returns:
        list of (str): the list of the day of the week
    """
    return ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


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


def validate_successful_response(res, current_page, page_size, maintainer_users, activity_seed, week_days):
    """Validates the general schema of a successful response for a request to the 
    GET /maintainer/<activity:id>/availabilities endpoint

    Args:
        res (any): the response to a request to the GET /maintainer/<activity:id>/availabilities endpoint
        current_page (int): The requested current_page
        page_size (int): The requested page_size
        maintainer_users (list of (dict of (str, str))): The list of users with role 'maintainer' in the database
        activity_seed (dict of (str, any)): The unassigned activity in the database
        week_days (str): The day of the week
    """
    assert res.status_code == 200
    assert len(res.get_json()['rows']) <= page_size
    assert res.get_json()['meta']['count'] == len(maintainer_users)
    assert res.get_json()['meta']['current_page'] == current_page
    assert res.get_json()['meta']['page_size'] == page_size
    expected_page_count = math.ceil(len(maintainer_users) / page_size)
    assert res.get_json()['meta']['page_count'] == expected_page_count

    for row in res.get_json()['rows']:
        assert "user" in row
        assert "password" not in row['user']
        assert "skill_compliance" in row
        assert "weekly_percentage_availability" in row
        assert type(row["weekly_percentage_availability"]) == dict
        for week_day in week_days:
            assert week_day in row["weekly_percentage_availability"].keys()
            assert "%" in row["weekly_percentage_availability"][week_day]
            assert type(row["weekly_percentage_availability"][week_day]) == str
            percentage_value = float(
                row["weekly_percentage_availability"][week_day].strip("%"))
            assert percentage_value >= 0 and percentage_value <= 100
        assert "week" in row
        assert str(row["week"]) == activity_seed["week"]


def test_no_activities_success(app, planner_client, maintainer_users, activity_seed, week_days):
    """ Tests a successful retrival of the weekly availabilities for a maintainer
    when there is no maintenance activity stored in the database
    """

    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    test_current_page = 1
    test_page_size = len(maintainer_users) - 1
    data = {"current_page": test_current_page, "page_size": test_page_size}

    res = planner_client.get(
        f"/maintainer/{activity_seed['activity_id']}/availabilities", data=data)

    validate_successful_response(
        res, test_current_page, test_page_size, maintainer_users, activity_seed, week_days)


def test_some_activities_success(app, planner_client, maintainer_user, maintainer_users, activity_seed, activity_seed_without_id, week_days):
    """ Tests a successful retrival of the weekly availabilities when a maintainer 
    is already associated to some activities 
    """
    start_time = config.MAINTAINER_WORK_START_HOUR
    end_time = start_time + config.MAINTAINER_WORK_HOURS

    with app.app_context():
        work_hours = config.MAINTAINER_WORK_HOURS
        i = start_time
        while i < end_time - 1:
            activity = MaintenanceActivityModel(**activity_seed_without_id)
            activity.maintainer_username = maintainer_user["username"]
            activity.week_day = "monday"
            activity.start_time = i
            activity.save_to_db()
            i += 1
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    test_current_page = 1
    test_page_size = len(maintainer_users)
    data = {"current_page": test_current_page, "page_size": test_page_size}

    res = planner_client.get(
        f"/maintainer/{activity_seed['activity_id']}/availabilities", data=data)

    validate_successful_response(
        res, test_current_page, test_page_size, maintainer_users, activity_seed, week_days)

    maintainer_availability = next(row["weekly_percentage_availability"] for row in res.get_json()[
                                   "rows"] if row["user"]["username"] == maintainer_user["username"])

    assert maintainer_availability["monday"] == f"{round(100 - 100*(work_hours-1)/work_hours)}%"


def test_full_activities_reassign(app, planner_client, maintainer_user, maintainer_users, activity_seed, activity_seed_without_id, week_days):
    """ Tests a successful retrival of the weekly availabilities when a maintainer
        already has a full schedule and the activity is already associated with that maintainer"""

    start_time = config.MAINTAINER_WORK_START_HOUR
    end_time = start_time + config.MAINTAINER_WORK_HOURS

    with app.app_context():
        work_hours = config.MAINTAINER_WORK_HOURS
        i = start_time
        while i < end_time - 1:
            activity = MaintenanceActivityModel(**activity_seed_without_id)
            activity.maintainer_username = maintainer_user["username"]
            activity.week_day = "monday"
            activity.start_time = i
            activity.save_to_db()
            i += 1
        activity = MaintenanceActivityModel(**activity_seed)
        activity.maintainer_username = maintainer_user["username"]
        activity.week_day = "monday"
        activity.start_time = i
        activity.save_to_db()

    test_current_page = 1
    test_page_size = len(maintainer_users)
    data = {"current_page": test_current_page, "page_size": test_page_size}

    res = planner_client.get(
        f"/maintainer/{activity_seed['activity_id']}/availabilities", data=data)

    validate_successful_response(
        res, test_current_page, test_page_size, maintainer_users, activity_seed, week_days)

    maintainer_availability = next(row["weekly_percentage_availability"] for row in res.get_json()[
                                   "rows"] if row["user"]["username"] == maintainer_user["username"])

    assert maintainer_availability["monday"] == f"{round(100 - 100*(work_hours-1)/work_hours)}%"


def test_full_activities_success(app, planner_client, maintainer_user, maintainer_users, activity_seed, activity_seed_without_id, week_days):
    """ Tests a successful retrival of the weekly availabilities when a maintainer
    has an already full schedule """
    start_time = config.MAINTAINER_WORK_START_HOUR
    end_time = start_time + config.MAINTAINER_WORK_HOURS

    with app.app_context():
        # Create many assigned activities without filling all the maintainer work schedule
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

    test_current_page = 1
    test_page_size = len(maintainer_users)
    data = {"current_page": test_current_page, "page_size": test_page_size}

    res = planner_client.get(
        f"/maintainer/{activity_seed['activity_id']}/availabilities", data=data)

    validate_successful_response(
        res, test_current_page, test_page_size, maintainer_users, activity_seed, week_days)

    maintainer_availability = next(row["weekly_percentage_availability"] for row in res.get_json()[
                                   "rows"] if row["user"]["username"] == maintainer_user["username"])

    assert maintainer_availability["monday"] == "0%"


def test_no_activities_page_not_found(app, planner_client, maintainer_users, activity_seed):
    """ Tests a failed retrival of the weekly availabilities given a non-existing current_page """

    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    test_current_page = 3
    test_page_size = len(maintainer_users)
    data = {"current_page": test_current_page, "page_size": test_page_size}

    res = planner_client.get(
        f"/maintainer/{activity_seed['activity_id']}/availabilities", data=data)

    assert res.status_code == 404
    assert "message" in res.get_json().keys()


def test_activity_not_found(planner_client):
    """ Tests a failed retrival of the weekly availabilities using an activity_id for an activity
    that does not exist"""

    unexisting_activity_id = 0

    res = planner_client.get(
        f"/maintainer/{unexisting_activity_id}/availabilities")

    assert res.status_code == 404
    assert "message" in res.get_json().keys()
    assert res.get_json()["message"] == "Activity not found"
