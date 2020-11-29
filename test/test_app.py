def test_unexisting_user_not_in_user_seeds(user_seeds, unexisting_user):
    """ unexisting_user's username should not be included among user_seeds usernames """
    filtered_users = list(filter(lambda user: user['username'] ==
                                 unexisting_user['username'], user_seeds))
    assert len(filtered_users) == 0
