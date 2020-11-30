def get_metadata(pagination):
    """Gets formatted metadata from pagination object in order to allow the frontend to handle pages properly

    Args:
        pagination (Pagination): Pagination object generated from query builders in models methods

    Returns:
        dict of (str, int): Metadata
    """
    return {
        "count": pagination.total,
        "current_page": pagination.page,
        "page_count": pagination.pages,
        "page_size": pagination.per_page
    }
