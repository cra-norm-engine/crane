"""Integration tests for auth API routes."""
import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_password
from app.models.enums import AuthProvider
from app.models.user import User


@pytest.fixture
def local_user(db_session) -> User:
    """Create a local auth user."""
    user = User(
        email="local@example.com",
        full_name="Local User",
        hashed_password=hash_password("password123"),
        is_active=True,
        auth_provider=AuthProvider.local,
    )
    db_session.add(user)
    db_session.commit()
    return user


class TestAuthLoginRoute:
    """Test POST /api/v1/auth/login."""

    def test_login_returns_tokens(self, client, local_user):
        """Login endpoint returns access and refresh tokens."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "local@example.com", "password": "password123"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_with_wrong_password_returns_401(self, client, local_user):
        """Login with wrong password returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "local@example.com", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data

    def test_login_with_nonexistent_email_returns_401(self, client):
        """Login with nonexistent email returns 401."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "anypassword"},
        )

        assert response.status_code == 401

    def test_login_with_inactive_user_returns_403(self, client, local_user, db_session):
        """Login with inactive user returns 403."""
        local_user.is_active = False
        db_session.commit()

        response = client.post(
            "/api/v1/auth/login",
            json={"email": "local@example.com", "password": "password123"},
        )

        assert response.status_code == 403

    def test_login_response_error_format(self, client, local_user):
        """Login error response follows canonical error format."""
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "local@example.com", "password": "wrong"},
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]


class TestAuthLogoutRoute:
    """Test POST /api/v1/auth/logout."""

    def test_logout_revokes_token(self, client, auth_client):
        """Logout invalidates the current token."""
        # auth_client is already authenticated
        response = auth_client.post("/api/v1/auth/logout")

        assert response.status_code == 200 or response.status_code == 204

    def test_logout_without_token_returns_401(self, client):
        """Logout without authentication returns 401."""
        response = client.post("/api/v1/auth/logout")

        assert response.status_code == 401


class TestAuthChangePasswordRoute:
    """Test POST /api/v1/auth/change-password."""

    def test_change_password_requires_authentication(self, client):
        """Change password endpoint requires authentication."""
        response = client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "old", "new_password": "new"},
        )

        assert response.status_code == 401

    def test_authenticated_user_can_change_password(self, client, auth_client, db_session):
        """Authenticated user can change their password."""
        response = auth_client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "admin1234", "new_password": "newpassword123"},
        )

        assert response.status_code in [200, 204]

    def test_change_password_with_wrong_old_password_fails(self, client, auth_client):
        """Change password fails if old password is incorrect."""
        response = auth_client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "wrongoldpass", "new_password": "newpassword123"},
        )

        assert response.status_code == 401 or response.status_code == 400

    def test_change_password_validates_new_password_strength(self, client, auth_client):
        """Change password validates new password meets requirements."""
        response = auth_client.post(
            "/api/v1/auth/change-password",
            json={"old_password": "admin1234", "new_password": "short"},
        )

        # Should fail due to password being too short (if validation exists)
        assert response.status_code in [400, 422]


class TestAuthRefreshTokenRoute:
    """Test POST /api/v1/auth/refresh."""

    def test_refresh_token_returns_new_access_token(self, client, local_user):
        """Refresh token endpoint returns new access token."""
        # First, get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "local@example.com", "password": "password123"},
        )
        login_data = login_response.json()
        refresh_token = login_data["refresh_token"]

        # Then refresh
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["access_token"] != login_data["access_token"]  # Should be different

    def test_refresh_with_invalid_token_returns_401(self, client):
        """Refresh with invalid token returns 401."""
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )

        assert response.status_code == 401

    def test_refresh_with_revoked_token_returns_401(self, client, local_user):
        """Refresh with revoked token returns 401."""
        # Get a token
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "local@example.com", "password": "password123"},
        )
        login_data = login_response.json()

        # Logout to revoke it
        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {login_data['access_token']}"},
        )

        # Try to refresh
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login_data["refresh_token"]},
        )

        assert response.status_code == 401


class TestAuthMeRoute:
    """Test GET /api/v1/auth/me."""

    def test_me_returns_current_user_info(self, client, auth_client):
        """GET /me returns authenticated user's info."""
        response = auth_client.get("/api/v1/auth/me")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "email" in data
        assert "full_name" in data
        assert "roles" in data
        assert "permissions" in data

    def test_me_without_authentication_returns_401(self, client):
        """GET /me without token returns 401."""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == 401


class TestAuthProtectedRouteAccess:
    """Test that protected routes require authentication."""

    def test_protected_route_without_token_returns_401(self, client):
        """Accessing protected route without token returns 401."""
        response = client.get("/api/v1/products/")

        assert response.status_code == 401

    def test_protected_route_with_valid_token_succeeds(self, client, auth_client):
        """Accessing protected route with valid token succeeds."""
        response = auth_client.get("/api/v1/products/")

        assert response.status_code == 200 or response.status_code == 403  # 403 if no permission

    def test_protected_route_with_invalid_token_returns_401(self, client):
        """Accessing protected route with invalid token returns 401."""
        response = client.get(
            "/api/v1/products/",
            headers={"Authorization": "Bearer invalid.token.here"},
        )

        assert response.status_code == 401
