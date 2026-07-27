from __future__ import annotations

from typing import Annotated

from pydantic import AfterValidator, Field

PASSWORD_REQUIREMENTS = (
    "Password must be at least 12 characters and include an uppercase letter, "
    "a lowercase letter, a number, and a special character."
)


def validate_password_complexity(password: str) -> str:
    checks = (
        len(password) >= 12,
        any(character.isupper() for character in password),
        any(character.islower() for character in password),
        any(character.isdigit() for character in password),
        any(not character.isalnum() and not character.isspace() for character in password),
    )
    if not all(checks):
        raise ValueError(PASSWORD_REQUIREMENTS)
    return password


StrongPassword = Annotated[
    str,
    Field(min_length=12, max_length=255),
    AfterValidator(validate_password_complexity),
]
