def test_app_runs(client):
    res = client.get('/users')
    assert res.status_code == 200
