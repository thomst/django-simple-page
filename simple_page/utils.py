import re


def camel_to_snake(name):
    """
    Convert a camel case string to snake case.
    """
    return re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()