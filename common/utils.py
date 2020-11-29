def get_metadata(pagination):
    # TODO: docstring
    return {
        "count": pagination.total,
        "current_page": pagination.page,
        "page_count": pagination.pages,
        "page_size": pagination.per_page
    }
