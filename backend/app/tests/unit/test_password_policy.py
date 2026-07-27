import pytest
from pydantic import ValidationError

from app.core.password_policy import validate_password_complexity
from app.schemas.admin_user import AdminUserCreate
from app.schemas.auth import AdminPasswordResetRequest, ChangePasswordRequest


def test_password_policy_accepts_all_required_character_classes():
    assert validate_password_complexity("SecurePass1!") == "SecurePass1!"


@pytest.mark.parametrize("password", ["Short1!", "lowercase123!", "UPPERCASE123!", "NoNumbersHere!", "NoSpecial1234"])
def test_password_policy_rejects_missing_requirement(password):
    with pytest.raises(ValueError):
        validate_password_complexity(password)


@pytest.mark.parametrize(
    ("schema", "payload"),
    [
        (ChangePasswordRequest, {"current_password": "old", "new_password": "weakpassword"}),
        (AdminPasswordResetRequest, {"new_password": "weakpassword"}),
        (AdminUserCreate, {"email": "user@example.com", "full_name": "User", "password": "weakpassword"}),
    ],
)
def test_all_password_writing_requests_enforce_policy(schema, payload):
    with pytest.raises(ValidationError):
        schema(**payload)
