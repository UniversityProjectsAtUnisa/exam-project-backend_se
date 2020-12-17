from exceptions.error import Error


class RoleError(Error):
    """Raised when the expected user's role does not match the current one"""
    pass
