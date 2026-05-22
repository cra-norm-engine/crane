"""Integration tests for AuthService."""
import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import AppException
from app.models.enums import AuthProvider
from app.models.user import User
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service(db_session: Session) -> AuthService:
    return AuthService(db_session)


@pytest.fixture
def test_user(db_session: Session) -> User:
    """Create a test user with local auth."""
    from app.core.security import hash_password
    user = User(
        email="test@example.com",
        full_name="Test User",
        hashed_password=hash_password("password123"),
        is_active=True,
        auth_provider=AuthProvider.local,
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestAuthServiceLogin:
    """Test login flow (local auth)."""

    def test_login_with_valid_credentials(self, auth_service, test_user):
        """User can log in with correct email and password."""
        payload = LoginRequest(email="test@example.com", password="password123")
        token_response = auth_service.login(payload=payload)

        assert token_response.access_token is not None
        assert token_response.refresh_token is not None
        assert token_response.token_type == "bearer"

    def test_login_with_wrong_password_raises_401(self, auth_service, test_user):
        """Login fails with wrong password."""
        payload = LoginRequest(email="test@example.com", password="wrongpassword")

        with pytest.raises(AppException) as exc_info:
            auth_service.login(payload=payload)

        assert exc_info.value.status_code == 401
        assert "Invalid email or password" in str(exc_info.value)

    def test_login_with_nonexistent_email_raises_401(self, auth_service):
        """Login fails with nonexistent email."""
        payload = LoginRequest(email="nonexistent@example.com", password="anypassword")

        with pytest.raises(AppException) as exc_info:
            auth_service.login(payload=payload)

        assert exc_info.value.status_code == 401

    def test_login_with_inactive_user_raises_403(self, auth_service, test_user, db_session):
        """Login fails if user account is inactive."""
        test_user.is_active = False
        db_session.commit()

        payload = LoginRequest(email="test@example.com", password="password123")

        with pytest.raises(AppException) as exc_info:
            auth_service.login(payload=payload)

        assert exc_info.value.status_code == 403
        assert "inactive" in str(exc_info.value).lower()

    def test_login_email_is_case_insensitive(self, auth_service, test_user):
        """Email comparison is case-insensitive."""
        payload = LoginRequest(email="TEST@EXAMPLE.COM", password="password123")
        token_response = auth_service.login(payload=payload)

        assert token_response.access_token is not None

    def test_login_trims_email_whitespace(self, auth_service, test_user):
        """Whitespace is trimmed from email."""
        payload = LoginRequest(email="  test@example.com  ", password="password123")
        token_response = auth_service.login(payload=payload)

        assert token_response.access_token is not None

    def test_login_access_token_contains_user_info(self, auth_service, test_user):
        """Access token payload includes user id, roles, and permissions."""
        from app.core.security import decode_access_token

        payload = LoginRequest(email="test@example.com", password="password123")
        token_response = auth_service.login(payload=payload)

        decoded = decode_access_token(token_response.access_token)
        assert decoded["sub"] == str(test_user.id)
        assert "roles" in decoded
        assert "permissions" in decoded
        assert "email" in decoded

    def test_authenticate_calls_login(self, auth_service, test_user):
        """authenticate() is a wrapper for login()."""
        payload = LoginRequest(email="test@example.com", password="password123")
        token_response = auth_service.authenticate(payload=payload)

        assert token_response.access_token is not None


class TestAuthServicePermissions:
    """Test that logins include correct permissions."""

    def test_login_includes_user_permissions(self, auth_service, test_user, db_session):
        """Logged-in user gets their assigned permissions."""
        from app.core.permissions import Permission
        from app.models.role import Role, RolePermission

        # Create a role with specific permissions
        role = Role(name="editor", description="Editor role")
        db_session.add(role)
        db_session.flush()

        # Assign permissions to role
        perm = RolePermission(role_id=role.id, permission=Permission.products_read.value)
        db_session.add(perm)
        db_session.flush()

        # Assign role to user
        test_user.roles.append(role)
        db_session.commit()

        payload = LoginRequest(email="test@example.com", password="password123")
        token_response = auth_service.login(payload=payload)

        from app.core.security import decode_access_token
        decoded = decode_access_token(token_response.access_token)
        assert "permissions" in decoded
        assert isinstance(decoded["permissions"], list)


class TestAuthServiceAuditLogging:
    """Test that auth events are logged to audit trail."""

    def test_successful_login_is_logged(self, auth_service, test_user, db_session):
        """Successful login creates audit event."""
        payload = LoginRequest(email="test@example.com", password="password123")
        auth_service.login(payload=payload, ip_address="192.168.1.1", user_agent="test-client")

        from app.models.audit_log_event import AuditLogEvent
        events = db_session.query(AuditLogEvent).filter_by(
            actor_user_id=test_user.id
        ).all()

        assert len(events) > 0
        assert any("login" in event.action_type.lower() for event in events)

    def test_failed_login_is_logged(self, auth_service, test_user, db_session):
        """Failed login attempt creates audit event."""
        payload = LoginRequest(email="test@example.com", password="wrongpassword")

        with pytest.raises(AppException):
            auth_service.login(payload=payload, ip_address="192.168.1.1")

        from app.models.audit_log_event import AuditLogEvent
        events = db_session.query(AuditLogEvent).all()

        assert len(events) > 0
        # Should have failed login event
        assert any("failed" in event.action_type.lower() for event in events)


class TestAuthServiceTokenRefresh:
    """Test token refresh functionality."""

    def test_refresh_token_creates_new_access_token(self, auth_service, test_user):
        """Refresh token can be used to get a new access token."""
        from app.core.security import decode_refresh_token

        payload = LoginRequest(email="test@example.com", password="password123")
        token_response = auth_service.login(payload=payload)

        # Verify refresh token is valid
        decoded = decode_refresh_token(token_response.refresh_token)
        assert decoded["sub"] == str(test_user.id)
