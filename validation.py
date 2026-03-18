import re


class ValidationError(Exception):
    pass


def validate_task_name(name: str) -> str:
    name = name.strip()
    if not name:
        raise ValidationError("Task name cannot be empty.")
    if len(name) > 100:
        raise ValidationError("Task name must be 100 characters or fewer.")
    if not re.match(r'^[\w\s\-\.\/\(\)\[\]#@&\+]+$', name):
        raise ValidationError("Task name contains invalid characters.")
    return name
