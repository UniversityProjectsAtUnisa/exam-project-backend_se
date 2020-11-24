def get_env_variable(name):
    """Makes the system crash if the environment is not set correctly
    
    Arguments:
        name {string} -- the environment variable to retrieve
    
    Raises:
        Exception: if the chosen environment variable is missing
    
    Returns:
        string -- the chosen environment variable
    """
    from os import environ
    
    try:
        return environ[name]
    except KeyError:
        message = "Expected environment variable '{}' not set.".format(name)
        print(message)
        return ""
