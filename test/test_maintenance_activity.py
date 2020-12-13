import pytest


@pytest.fixture
def activity_seeds():
    """Gets the list of activities that will be used to prepopulate the database before each test

    Returns:
        list of (dict of (str, str)): list of activities
    """
    return [
        {'activity_id': '1', 'activity_type': 'planned', 'site': 'management',
            'typology': 'electrical', 'description': 'Planned electrical Maintenance Activity', 'estimated_time': '30',
            'interruptible': 'yes', 'materials': 'drill', 'week': '43', 'workspace_notes': 'Site: Management; Typology: Electrical'},

        {'activity_id': '2', 'activity_type': 'unplanned', 'site': 'management',
            'typology': 'electrical', 'description': 'Unplanned electrical Maintenance Activity', 'estimated_time': '45',
            'interruptible': 'no', 'materials': 'drill', 'week': '38', 'workspace_notes': 'Site: Management; Typology: Electrical'},

        {'activity_id': '3', 'activity_type': 'extra', 'site': 'management',
            'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
            'interruptible': 'yes', 'materials': 'spikes', 'week': '20', 'workspace_notes': 'Site: Management; Typology: Electrical'},

        # {'activity_id': '4', 'activity_type': 'extra', 'site': 'management',
        #    'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
        #    'interruptible': 'yes', 'materials': 'drill', 'week': '43', 'workspace_notes': 'Site: Management; Typology: Electrical'},

    ]


@pytest.fixture
def unexisting_activity():
    """Gets an activity that is not included in activity_seeds

    Returns:
        dict of (str, str): the unexisting_activity
    """
    return {'activity_type': 'planned', 'site': 'management',
            'typology': 'electronical', 'description': 'Planned electronical Maintenance Activity', 'estimated_time': '120',
            'interruptible': 'yes', 'materials': 'spikes', 'week': '43', 'workspace_notes': 'Site: Management; Typology: Electronical'}


@pytest.fixture(autouse=True)
def setup(app, activity_seeds):
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
    return True


def test_unexisting_activity(activity_seeds, unexisting_activity):
    """ unexisting_activity's id should not be included among activity_seeds identifiers """
    filtered_activity = list(filter(lambda activity: activity['activity_id'] ==
                                    unexisting_activity['activity_id'], activity_seeds))
    assert len(filtered_activity) == 0


def test_get_activity_success(client, activity_seeds):
    """ Test for searching an existing activity by his id """
    test_activity = activity_seeds[0]
    res = client.get(f"/activity/{test_activity['activity_id']}")
    assert res.status_code == 200
    assert res.get_json()['activity_id'] == test_activity['activity_id']


def test_get_activity_not_found(client, unexisting_activity):
    """ Test for searching a non-existing activity """
    test_activity = unexisting_activity
    res = client.get(f"/activity/{test_activity['activity_id']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()


def test_get_activities_success(client, activity_seeds):
    """ Test for getting correctly the first page of activities """
    test_current_page = 1
    test_page_size = len(activity_seeds) - 1

    res = client.get(
        f"/activities?current_page={test_current_page}&page_size={test_page_size}")

    assert res.status_code == 200
    assert len(res.get_json()['rows']) <= test_page_size
    assert res.get_json()['meta']['count'] == len(activity_seeds)
    assert res.get_json()['meta']['current_page'] == test_current_page
    assert res.get_json()['meta']['page_size'] == test_page_size

    import math
    expected_page_count = math.ceil(len(activity_seeds) / test_page_size)
    assert res.get_json()['meta']['page_count'] == expected_page_count


def test_get_activities_page_not_found(client, activity_seeds):
    """ Test for a non-existing page """
    test_page_size = 5
    import math
    test_page_count = math.ceil(len(activity_seeds) / test_page_size)
    test_current_page = test_page_count + 1
    res = client.get(
        f"/activities?current_page={test_current_page}&page_size={test_page_size}")

    assert res.status_code == 404
    assert "message" in res.get_json().keys()


def test_post_activity_success(client, unexisting_activity):
    """ Test for creating a new activity with a non-existing id """
    test_activity = unexisting_activity
    res = client.post('/activity', data=test_activity)

    assert res.status_code == 201
    assert res.get_json()['activity_id'] == test_activity['activity_id']


def test_post_activity_already_exists(client, activity_seeds):
    """ Test for creating a new activity with an existing id """
    test_activity = activity_seeds[0]
    res = client.post('/activity', data=test_activity)

    assert res.status_code == 400
    assert 'message' in res.get_json().keys()


def test_post_activity_missing_id(client):
    """ Test for creating a new activity without id """
    test_activity_without_id = {'activity_type': 'extra', 'site': 'management',
                                'typology': 'electrical', 'description': 'Extra electrical Maintenance Activity', 'estimated_time': '60',
                                'interruptible': 'yes', 'materials': 'spikes', 'week': '20',
                                'workspace_notes': 'Site: Management; Typology: Electrical'}
    res = client.post('/activity', data=test_activity_without_id)
    assert res.status_code == 400
    assert 'message' in res.get_json().keys()
    assert 'id' in res.get_json()['activity_id'].keys()


def test_put_activity_id_success(client, unexisting_activity, activity_seeds):
    """ Test for modifying an activity's workspace notes 
    TODO
    """
    test_activity = {'workspace_notes': unexisting_activity['workspace_notes']}
    test_old_activity = activity_seeds[0]

    res = client.put(
        f"/activity/{test_old_activity['workspace_notes']}", data=test_activity)
    assert res.status_code == 200
    assert res.get_json()[
        'workspace_notes'] == test_old_activity['workspace_notes']


def test_delete_activity_success(client, activity_seeds):
    """ Test for deleting an existing activity """
    test_activity = activity_seeds[0]
    res = client.delete(f"/activity/{test_activity['activity_id']}")
    assert res.status_code == 200
    assert 'message' in res.get_json().keys()


def test_delete_activity_not_found(client, unexisting_activity):
    """ Test for deleting a non-existing activity """
    test_activity = unexisting_activity
    res = client.delete(f"/activity/{test_activity['activity_id']}")
    assert res.status_code == 404
    assert 'message' in res.get_json().keys()


def test_week(client, activity_seeds, unexisting_activity):
    test_activity = unexisting_activity
    res = client.get(f"/activities?week={test_activity['week']}")
    assert res.status_code == 200
    assert len(res.get_json()['rows']) <= len(activity_seeds)
    #assert res.get_json()['week'] == test_activity['week']
