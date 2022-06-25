_number_in_search = 0


def get_number_in_search() -> int:
    return _number_in_search


def increase_number_in_search(*args, **kwargs):
    global _number_in_search

    _number_in_search += 1


def decrease_number_in_search(*args, **kwargs):
    global _number_in_search

    _number_in_search -= 1
