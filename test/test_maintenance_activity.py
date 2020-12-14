import pytest


@pytest.fixture
def activity_seeds():
    """Gets the list of activities that will be used to prepopulate the database before each test

    Returns:
        list of (dict of (str, str)): list of activities
    """
    return [
        {'activity_id': '101', 'activity_type': 'planned', 'site': 'management',
            'typology': 'electrical', 'description': 'Planned electrical Maintenance Activity', 'estimated_time': '30',
            'interruptible': 'yes', 'materials': 'drill', 'week': '1', 'workspace_notes': 'Site: Management; Typology: Electrical'},

        {'activity_id': '102', 'activity_type': 'unplanned', 'site': 'management',
            'typology': 'electrical', 'description': 'Unplanned electrical Maintenance Activity', 'estimated_time': '45',
            'interruptible': 'no', 'materials': 'drill', 'week': '2', 'workspace_notes': 'Site: Management; Typology: Electrical'},

        {'activity_id': '103', 'activity_type': 'extra', 'site': 'management',
            'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
            'interruptible': 'yes', 'materials': 'spikes', 'week': '3', 'workspace_notes': 'Site: Management; Typology: Electrical'},

    ]


@pytest.fixture
def unexisting_activity():
    """Gets an activity that is not included in activity_seeds

    Returns:
        dict of (str, str): the unexisting activity
    """
    return {'activity_id': '500', 'activity_type': 'planned', 'site': 'management',
            'typology': 'electronical', 'description': 'Planned electronical Maintenance Activity', 'estimated_time': '120',
            'interruptible': 'yes', 'materials': 'spikes', 'week': '30', 'workspace_notes': 'Site: Management; Typology: Electronical'}


@pytest.fixture
def unexisting_activity_without_id():
    """Gets an activity that is not included in activity_seeds and does not have an activity_id

    Returns:
        dict of (str, str): the unexisting activity without id
    """
    return {'activity_type': 'extra', 'site': 'management',
            'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
            'interruptible': 'yes', 'materials': 'spikes', 'week': '20',
            'workspace_notes': 'Site: Management; Typology: Electrical'}


@pytest.fixture
def post_required_arguments():
    """List of body params required in order to perform a post request

    Returns:
        list of (str): The list of arguments
    """
    return ["activity_type",
            "site",
            "typology",
            "description",
            "estimated_time",
            "interruptible",
            "week",
            ]


@pytest.fixture
def post_optional_arguments():
    """List of optional body params in order taken by a post request

    Returns:
        list of (str): The list of arguments
    """
    return [
        "materials",
        "workspace_notes"
    ]


@pytest.fixture
def planner_seed():
    """Gets the mock planner user that will be used to prepopulate the database before each test

    Returns:
        (dict of (str, str):  mock planner user
    """
    return {'username': 'planner', 'password': 'password', 'role': 'planner'}


@pytest.fixture(autouse=True)
def setup(app, activity_seeds, planner_seed):
    """Before each test it drops every table and recreates them. 
    Then it creates an activity for every dictionary present in activity_seeds

    Returns:
        boolean: the return status
    """
    with app.app_context():
        from db import db
        db.drop_all()
        db.create_all()
        from models.maintenance_activity import MaintenanceActivityModel
        for seed in activity_seeds:
            activity = MaintenanceActivityModel(**seed)
            activity.save_to_db()
        from models.user import UserModel
        planner = UserModel(**planner_seed)
        planner.save_to_db()
    return True


@pytest.fixture
def planner_client(client, planner_seed):
    """ Creates a test client with preset planner authorization headers taken from the login endpoint 

    Returns:
        FlaskClient: The test client
    """
    res = client.post(
        "/login", data=planner_seed)
    access_token = res.get_json()["access_token"]
    client.environ_base['HTTP_AUTHORIZATION'] = 'Bearer ' + access_token
    return client


def test_unexisting_activity(activity_seeds, unexisting_activity):
    """ unexisting_activity's id should not be included among activity_seeds identifiers """
    filtered_activities = list(filter(lambda activity: activity['activity_id'] ==
                                      unexisting_activity['activity_id'], activity_seeds))
    assert len(filtered_activities) == 0


def test_get_activity_success(planner_client, activity_seeds):
    """ Test for searching an existing activity by his id """
    test_activity: dict = activity_seeds[0]
    res = planner_client.get(f"/activity/{test_activity['activity_id']}")
    assert res.status_code == 200
    activity_json = res.get_json()
    for k in test_activity.keys():
        assert str(activity_json[k]) == test_activity[k]


def test_get_activity_not_found(planner_client, unexisting_activity):
    """ Test for searching a non-existing activity """
    test_activity = unexisting_activity
    res = planner_client.get(f"/activity/{test_activity['activity_id']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()


def test_get_activities_success(planner_client, activity_seeds):
    """ Test for getting correctly the first page of activities """
    test_current_page = 1
    test_page_size = len(activity_seeds) - 1

    res = planner_client.get(
        f"/activities?current_page={test_current_page}&page_size={test_page_size}")

    assert res.status_code == 200
    assert len(res.get_json()['rows']) <= test_page_size
    assert res.get_json()['meta']['count'] == len(activity_seeds)
    assert res.get_json()['meta']['current_page'] == test_current_page
    assert res.get_json()['meta']['page_size'] == test_page_size

    import math
    expected_page_count = math.ceil(len(activity_seeds) / test_page_size)
    assert res.get_json()['meta']['page_count'] == expected_page_count


def test_get_activities_in_week_success(planner_client, activity_seeds):
    test_activity = activity_seeds[0]
    res = planner_client.get(f"/activities?week={test_activity['week']}")
    assert res.status_code == 200
    for activity in res.get_json()['rows']:
        assert str(activity["week"]) == test_activity["week"]


def test_get_activities_page_not_found(planner_client, activity_seeds):
    """ Test for a non-existing page """
    test_page_size = 5
    import math
    test_page_count = math.ceil(len(activity_seeds) / test_page_size)
    test_current_page = test_page_count + 1
    res = planner_client.get(
        f"/activities?current_page={test_current_page}&page_size={test_page_size}")

    assert res.status_code == 404
    assert "message" in res.get_json().keys()


def test_post_activity_success(planner_client, unexisting_activity_without_id):
    """ Test for creating a new activity """
    test_activity = unexisting_activity_without_id
    res = planner_client.post('/activity', data=test_activity)

    assert res.status_code == 201
    activity_json = res.get_json()
    for k in test_activity.keys():
        assert test_activity[k] == str(
            activity_json[k]), f"'{k}' for the created activity does not match the one sent to the post request, {test_activity[k]} != {activity_json[k]}"


def test_post_activity_missing_required_argument(planner_client, unexisting_activity_without_id, post_required_arguments):
    """ Test for creating a new activity without a required argument """
    import copy
    for arg in post_required_arguments:
        test_activity = copy.deepcopy(unexisting_activity_without_id)
        del test_activity[arg]
        res = planner_client.post('/activity', data=test_activity)
        assert res.status_code == 400, f"Status code is not 400 when omitting required parameter '{arg}'"
        assert 'message' in res.get_json().keys(
        ), f"There is no error message in the response when omitting required parameter '{arg}'"
        assert arg in res.get_json()['message'].keys(
        ), f"The error message does not mention that the required parameter '{arg}' is missing"


def test_post_activity_missing_optional_argument(planner_client, unexisting_activity_without_id, post_optional_arguments):
    """ Test for creating a new activity without an optional argument """
    import copy
    for arg in post_optional_arguments:
        test_activity = copy.deepcopy(unexisting_activity_without_id)
        del test_activity[arg]
        res = planner_client.post('/activity', data=test_activity)
        assert res.status_code == 201, f"Status code is not 201 when omitting optional parameter '{arg}'"
        activity_json = res.get_json()
        for k in test_activity.keys():
            assert test_activity[k] == str(
                activity_json[k]), f"'{k}' for the created activity does not match the one sent to the post request when omitting the optional parameter , {test_activity[k]} != {activity_json[k]}"


def test_put_activity_id_success(planner_client, unexisting_activity, activity_seeds):
    """ Test for modifying an activity's workspace notes """
    test_activity = {'workspace_notes': unexisting_activity['workspace_notes']}
    test_old_activity = activity_seeds[0]

    res = planner_client.put(
        f"/activity/{test_old_activity['activity_id']}", data=test_activity)
    assert res.status_code == 200
    assert res.get_json()[
        'workspace_notes'] == test_activity['workspace_notes']


def test_delete_activity_success(planner_client, activity_seeds):
    """ Test for deleting an existing activity """
    test_activity = activity_seeds[0]
    res = planner_client.delete(f"/activity/{test_activity['activity_id']}")
    assert res.status_code == 200
    assert 'message' in res.get_json().keys()


def test_delete_activity_not_found(planner_client, unexisting_activity):
    """ Test for deleting a non-existing activity """
    test_activity = unexisting_activity
    res = planner_client.delete(f"/activity/{test_activity['activity_id']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()
