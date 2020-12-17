from test.test_maintenance_activity import unexisting_activity
import pytest
import config
from models.maintenance_activity import MaintenanceActivityModel
import math


@pytest.fixture
def user_seeds():
    """Gets a list of users for every possible role

    Returns:
        list of (dict of (str, str)): list of users
    """
    return [
        {'username': 'admin', 'password': 'password', 'role': 'admin'},
        {'username': 'planner', 'password': 'password', 'role': 'planner'},
        {'username': 'maintainer', 'password': 'password', 'role': 'maintainer'},
    ]


@pytest.fixture
def activity_seed():
    """Gets an activity with preset activity_id

    Returns:
        dict of (str, any): the activity with activity_id
    """
    return {'activity_id': "101", 'activity_type': 'extra', 'site': 'management',
            'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
            'interruptible': True, 'materials': 'spikes', 'week': '20',
            'workspace_notes': 'Site: Management; Typology: Electrical'}


@pytest.fixture
def activity_seed_without_id():
    """Gets an activity without preset activity_id

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


def test_no_activities_success(app, planner_client, maintainer_user, activity_seed, week_days):
    """ Tests a successful retrival of the daily availabilities for a maintainer 
    when there is no maintenance activity stored in the database 
    """

    start_time = config.MAINTAINER_WORK_START_HOUR
    end_time = start_time + config.MAINTAINER_WORK_HOURS

    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    for week_day in week_days:
        data = {
            "activity_id": activity_seed["activity_id"], "week_day": week_day}
        res = planner_client.get(
            f"/maintainer/{maintainer_user['username']}/availability", data=data)

        assert res.status_code == 200
        assert set(str(time) for time in range(start_time, end_time)) == set(
            res.get_json().keys())
        for k in res.get_json().keys():
            assert res.get_json()[k] == 60


def test_some_activities_success(app, planner_client, maintainer_user, activity_seed_without_id, activity_seed, week_days):
    """ Tests a successful retrival of the daily availabilities for a maintainer 
    who is already associated to some activities """

    start_time = config.MAINTAINER_WORK_START_HOUR
    end_time = start_time + config.MAINTAINER_WORK_HOURS

    with app.app_context():
        # Create many assigned activities and assign them to a maintainer without filling his work schedule
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

    # Make a request for every day of the week
    for week_day in week_days:
        data = {
            "activity_id": activity_seed["activity_id"], "week_day": week_day}
        res = planner_client.get(
            f"/maintainer/{maintainer_user['username']}/availability", data=data)

        assert res.status_code == 200
        # An availability is stated for every work hour
        assert set(str(time) for time in range(start_time, end_time)) == set(
            res.get_json().keys())
        for k in res.get_json().keys():
            if int(k) == end_time-1 or week_day != 'monday':
                assert int(res.get_json()[k]) == 60, f"{week_day}, {k}"
            else:
                assert int(res.get_json()[k]) == 0, f"{week_day}, {k}"


def test_full_activities_success(app, planner_client, maintainer_user, activity_seed_without_id, activity_seed, week_days):
    """ Tests a successful retrival of the daily availability for a maintainer
    who already has a full schedule """

    start_time = config.MAINTAINER_WORK_START_HOUR
    end_time = start_time + config.MAINTAINER_WORK_HOURS

    with app.app_context():
        # Create many assigned activities and assign them to a maintainer in order to fill his work schedule
        for week_day in week_days:
            i = start_time
            while i < end_time:
                activity = MaintenanceActivityModel(**activity_seed_without_id)
                activity.maintainer_username = maintainer_user["username"]
                activity.week_day = week_day
                activity.start_time = i
                activity.save_to_db()
                i += 1
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    # Make a request for every day of the week
    for week_day in week_days:
        data = {
            "activity_id": activity_seed["activity_id"], "week_day": week_day}
        res = planner_client.get(
            f"/maintainer/{maintainer_user['username']}/availability", data=data)

        assert res.status_code == 200
        # An availability is stated for every work hour
        assert set(str(time) for time in range(start_time, end_time)) == set(
            res.get_json().keys())
        for k in res.get_json().keys():
            assert int(res.get_json()[k]) == 0, f"{week_day}, {k}"


def test_full_activities_reassign_activity_success(app, planner_client, maintainer_user, activity_seed_without_id, activity_seed):
    """ Tests a successful retrival of the daily availability for a maintainer 
    who already has a full schedule, when the activity is already associated with the maintainer """

    start_time = config.MAINTAINER_WORK_START_HOUR
    end_time = start_time + config.MAINTAINER_WORK_HOURS

    with app.app_context():
        # Create many assigned activities and assign them to a maintainer in order to fill his work schedule
        i = start_time
        while i < end_time - 1:
            activity = MaintenanceActivityModel(**activity_seed_without_id)
            activity.maintainer_username = maintainer_user["username"]
            activity.week_day = "monday"
            activity.start_time = i
            activity.save_to_db()
            i += 1
        # Create one last activity activity with known id and associate it to the user
        # in order to fill completely his daily work schedule
        activity = MaintenanceActivityModel(**activity_seed)
        activity.maintainer_username = maintainer_user["username"]
        activity.week_day = "monday"
        activity.start_time = i
        activity.save_to_db()

    data = {
        "activity_id": activity_seed["activity_id"], "week_day": "monday"}
    res = planner_client.get(
        f"/maintainer/{maintainer_user['username']}/availability", data=data)

    # An availability is stated for every work hour
    assert set(str(time) for time in range(start_time, end_time)) == set(
        res.get_json().keys())
    for k in res.get_json().keys():
        if int(k) == end_time-1:
            assert int(res.get_json()[k]) == 60
        else:
            assert int(res.get_json()[k]) == 0


def test_multiple_assignment_same_time(app, planner_client, activity_seed, maintainer_user):
    """ Tests a successful retrival of the daily availability for a maintainer 
    who is already associated with two maintenance activities that start in the same hour  """

    test_activity_without_id = {'activity_type': 'extra', 'site': 'management',
                                'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '50',
                                'interruptible': True, 'materials': 'spikes', 'week': '20',
                                'workspace_notes': 'Site: Management; Typology: Electrical'}
    with app.app_context():
        start_time = config.MAINTAINER_WORK_START_HOUR
        end_time = start_time + config.MAINTAINER_WORK_HOURS
        # Create two activities and associate them to the user
        # having them to start at the same time
        for _ in range(2):
            activity = MaintenanceActivityModel(**test_activity_without_id)
            activity.maintainer_username = maintainer_user["username"]
            activity.week_day = "monday"
            activity.start_time = start_time
            activity.save_to_db()
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "activity_id": activity_seed["activity_id"], "week_day": "monday"}
    res = planner_client.get(
        f"/maintainer/{maintainer_user['username']}/availability", data=data)

    assert res.status_code == 200
    # An availability is stated for every work hour
    assert set(str(time) for time in range(start_time, end_time)) == set(
        res.get_json().keys())
    for k in res.get_json().keys():
        if int(k) == start_time:
            assert int(res.get_json()[k]) == 0
        elif int(k) == start_time + 1:
            # The busy time overflows correctly
            assert int(res.get_json()[k]) == 20
        else:
            assert int(res.get_json()[k]) == 60


def test_wrong_user_role(app, planner_client, planner_user, activity_seed):
    """ Tests a failed retrival of the daily availability for an user whose role is not 'maintainer' """

    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "activity_id": activity_seed["activity_id"], "week_day": "monday"}
    res = planner_client.get(
        f"/maintainer/{planner_user['username']}/availability", data=data)

    assert res.status_code == 400
    assert "message" in res.get_json()


def test_user_not_found(app, planner_client, activity_seed):
    """ Tests a failed retrival of the daily availability for an user that does not exist """
    unexisting_user_id = 0

    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "activity_id": activity_seed["activity_id"], "week_day": "monday"}
    res = planner_client.get(
        f"/maintainer/{unexisting_user_id}/availability", data=data)

    assert res.status_code == 404
    assert "message" in res.get_json()


def test_activity_not_found(app, planner_client, maintainer_user, activity_seed):
    """ Tests a failed retrival of the daily availability given that the planner
    wants to assign him an activity that does not exist """
    unexisting_activity_id = 0

    with app.app_context():
        # Create one unassigned activity
        activity = MaintenanceActivityModel(**activity_seed)
        activity.save_to_db()

    data = {
        "activity_id": unexisting_activity_id, "week_day": "monday"}
    res = planner_client.get(
        f"/maintainer/{maintainer_user['username']}/availability", data=data)

    assert res.status_code == 404
    assert "message" in res.get_json()
