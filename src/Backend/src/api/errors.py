"""
Module containing known errors.
"""

import typing


class BaseError(Exception):
    """
    Base error for custom exceptions.
    """

    output: dict[str, typing.Any]


class NotFound(BaseError):
    """
    Error to be returned when a resource is not found.
    """

    def __init__(self, entity: str | None = None) -> None:
        self.output = {
            "status_code": 404,
            "message": (
                "The entity was not found."
                if not entity
                else f"The entity {entity.capitalize()} was not found."
            ),
            "code": "not_found" if not entity else f"{entity}_not_found",
        }


class NotSupported(BaseError):
    """
    Error to be returned when this type is not supported.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 400,
            "message": "This extension is not supported.",
            "code": "not_supported",
        }


class InvalidResetUrl(BaseError):
    """
    Error to be returned when this type is not supported.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 400,
            "message": "This is an invalid reset link.",
            "code": "invalid_reset_link",
        }


class CantDeleteYourself(BaseError):
    """
    Error to be returned when a user tries to delete himself.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 400,
            "message": "You can't delete your own user.",
            "code": "cant_delete_user",
        }


class CantDelete(BaseError):
    """
    Error to be returned when a user tries to delete
    a resource related to other existant resources.
    """

    def __init__(self, resource: str, conencted_with: str) -> None:
        self.output = {
            "status_code": 400,
            "message": (
                f"You can't delete {resource} due to "
                f"being connected with {conencted_with}."
            ),
            "code": "cant_delete_resource",
        }


class NotPending(BaseError):
    """
    Error to be returned when a resource is not found.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 404,
            "message": "Exam/Question not pending or doesn't exist.",
            "code": "exam_or_question_doesnt_exist",
        }


class AlreadyExists(BaseError):
    """
    Error to be returned when a resource already exists.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 409,
            "message": "The entity already exists.",
            "code": "already_exists",
        }


class TokenExpired(BaseError):
    """
    Expired token.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 401,
            "message": "The token is expired and/or invalid.",
            "code": "token_expired_or_invalid",
        }


class SessionExpired(BaseError):
    """
    Expired token.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 401,
            "message": "The session is expired.",
            "code": "session_expired",
        }


class FieldNotNullable(BaseError):
    """
    Field cannot be null.
    """

    def __init__(self, field: str | None = None) -> None:
        self.output = {
            "status_code": 422,
            "message": (
                "One or more fields sent are null and aren't nullable."
                if not field
                else f"The field {field} cannot be null."
            ),
            "code": "field_not_nullable",
        }


class FieldShouldBeLenghtier(BaseError):
    """
    Field cannot be null.
    """

    def __init__(self, field: str, min_length: int) -> None:
        self.output = {
            "status_code": 422,
            "message": (
                f"The field {field} should be at least {min_length} characters long."
            ),
            "code": "field_should_be_lenghtier",
        }


class InvalidGroupOrg(BaseError):
    """
    Field cannot be null.
    """

    def __init__(self, field: str) -> None:
        self.output = {
            "status_code": 422,
            "message": f"This kind of user can only have 1, and only 1, {field}.",
            "code": "invalid_group_org",
        }


class InvalidModelId(BaseError):
    """
    Field cannot be null.
    """

    def __init__(self, model: str) -> None:
        self.output = {
            "status_code": 400,
            "message": f"Invalid identifier for {model}.",
            "code": f"invalid_{model}_id",
        }


class InvalidChosenGroup(BaseError):
    """
    Field cannot be null.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 422,
            "message": (
                "The chosen groups must be related with the chosen organizations."
            ),
            "code": "invalid_chosen_group",
        }


class InvalidField(BaseError):
    """
    Field filled with invalid data.
    """

    def __init__(self, field: str | None = None) -> None:
        self.output = {
            "status_code": 422,
            "message": (
                "One or more fields sent are invalids."
                if not field
                else f"The field {field} is invalid."
            ),
            "code": "invalid_field",
        }


class InvalidCredentials(BaseError):
    """
    Invalid credentials.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 401,
            "message": "Your email and/or password are invalid.",
            "code": "email_or_password_invalid",
        }


class Forbidden(BaseError):
    """
    Invalid credentials.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 403,
            "message": "You don't have permission to perform this action.",
            "code": "forbidden",
        }


class GroupValidationError(BaseError):
    """
    Error to be returned when a default user doesn't have group.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 400,
            "message": "The user must have a group.",
            "code": "user_must_have_a_group",
        }


class StartDateError(BaseError):
    """
    Error raised when start date is before end date.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 400,
            "message": "Start date must be before the end date.",
            "code": "start_date_error",
        }


class CantEditExam(BaseError):
    """
    Error raised when editing an exam that is already in progress.
    """

    def __init__(self) -> None:
        self.output = {
            "status_code": 400,
            "message": "Can't edit exam after start date.",
            "code": "cant_edit_after_start_date",
        }
