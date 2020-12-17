from exceptions.error import Error


class InvalidAgendaError(Error):
    """Raised when the maintainer agenda overflows"""

    message = "The maintainer does not have enough time to perform every maintenance activity"

    def __init__(self):
        super().__init__(self.message)
