from __future__ import annotations

import logging

import ldap3
from ldap3 import AUTO_BIND_NO_TLS, AUTO_BIND_TLS_BEFORE_BIND, Connection, Server, Tls
from ldap3.core.exceptions import LDAPBindError, LDAPException, LDAPSocketOpenError

from app.core.config import settings

log = logging.getLogger(__name__)


class LDAPConnectionError(Exception):
    """Raised when the LDAP server cannot be reached."""


class LDAPAuthError(Exception):
    """Raised when LDAP credentials are invalid."""


def _build_server() -> Server:
    # For ldaps:// the SSL layer is established at socket level — no Tls() needed.
    # For ldap:// + STARTTLS, attach a Tls() object so ldap3 can upgrade the connection.
    use_starttls = settings.ldap_use_tls and not settings.ldap_server_url.startswith("ldaps://")
    tls = Tls() if use_starttls else None
    return Server(
        settings.ldap_server_url,
        tls=tls,
        connect_timeout=settings.ldap_connection_timeout,
        get_info=ldap3.NONE,
    )


def _auto_bind() -> str:
    """Return the correct auto_bind constant for the configured transport."""
    if settings.ldap_use_tls and not settings.ldap_server_url.startswith("ldaps://"):
        return AUTO_BIND_TLS_BEFORE_BIND  # STARTTLS: upgrade before bind
    return AUTO_BIND_NO_TLS  # plain ldap:// or ldaps:// (SSL already at socket level)


def test_connection() -> dict:
    """
    Attempt a service-account bind and return a status dict.
    Used by the admin /admin/ldap/status endpoint.
    """
    if not settings.ldap_enabled:
        return {"enabled": False, "connected": False, "message": "LDAP is disabled"}

    try:
        server = _build_server()
        conn = Connection(
            server,
            user=settings.ldap_bind_dn,
            password=settings.ldap_bind_password,
            auto_bind=_auto_bind(),
            raise_exceptions=True,
        )
        conn.unbind()
        return {
            "enabled": True,
            "connected": True,
            "server": settings.ldap_server_url,
            "base_dn": settings.ldap_base_dn,
            "message": "Connection successful",
        }
    except LDAPSocketOpenError as exc:
        log.warning("LDAP connection failed: %s", exc)
        return {
            "enabled": True,
            "connected": False,
            "server": settings.ldap_server_url,
            "message": f"Cannot reach server: {exc}",
        }
    except LDAPBindError as exc:
        log.warning("LDAP service-account bind failed: %s", exc)
        return {
            "enabled": True,
            "connected": False,
            "server": settings.ldap_server_url,
            "message": f"Service-account bind failed: {exc}",
        }
    except LDAPException as exc:
        log.error("Unexpected LDAP error: %s", exc)
        return {
            "enabled": True,
            "connected": False,
            "server": settings.ldap_server_url,
            "message": f"LDAP error: {exc}",
        }


def authenticate_user(email: str, password: str) -> dict | None:
    """
    Authenticate a user against LDAP.
    Returns a dict with {email, full_name} on success, or None on failure.
    Raises LDAPConnectionError if the server is unreachable.
    """
    if not settings.ldap_enabled:
        return None

    try:
        server = _build_server()

        # Step 1: bind as service account to find the user's DN
        svc_conn = Connection(
            server,
            user=settings.ldap_bind_dn,
            password=settings.ldap_bind_password,
            auto_bind=_auto_bind(),
            raise_exceptions=True,
        )

        search_filter = settings.ldap_user_filter.replace("{email}", _escape_filter(email))
        attrs = [settings.ldap_attr_email, settings.ldap_attr_full_name]

        svc_conn.search(
            search_base=settings.ldap_base_dn,
            search_filter=search_filter,
            attributes=attrs,
        )

        if not svc_conn.entries:
            svc_conn.unbind()
            return None

        entry = svc_conn.entries[0]
        user_dn = entry.entry_dn
        raw_email = _attr_value(entry, settings.ldap_attr_email) or email
        full_name = _attr_value(entry, settings.ldap_attr_full_name) or email
        svc_conn.unbind()

        # Step 2: bind as the user to verify their password
        user_conn = Connection(
            server,
            user=user_dn,
            password=password,
            auto_bind=_auto_bind(),
            raise_exceptions=True,
        )
        user_conn.unbind()

        return {"email": raw_email.lower(), "full_name": full_name}

    except LDAPSocketOpenError as exc:
        raise LDAPConnectionError(f"Cannot reach LDAP server: {exc}") from exc
    except LDAPBindError:
        # user bind failed → wrong password
        return None
    except LDAPException as exc:
        log.error("LDAP authentication error for %s: %s", email, exc)
        return None


def search_users(search: str = "") -> list[dict]:
    """
    Search LDAP for users matching *search* (substring match on email/displayName).
    Returns a list of {email, full_name} dicts.
    Used by admin sync endpoint.
    Raises LDAPConnectionError if the server is unreachable.
    """
    if not settings.ldap_enabled:
        return []

    try:
        server = _build_server()
        conn = Connection(
            server,
            user=settings.ldap_bind_dn,
            password=settings.ldap_bind_password,
            auto_bind=_auto_bind(),
            raise_exceptions=True,
        )

        if search:
            esc = _escape_filter(search)
            search_filter = (
                f"(&(objectClass=person)"
                f"(|({settings.ldap_attr_email}=*{esc}*)"
                f"({settings.ldap_attr_full_name}=*{esc}*)))"
            )
        else:
            search_filter = "(objectClass=person)"

        attrs = [settings.ldap_attr_email, settings.ldap_attr_full_name]
        conn.search(
            search_base=settings.ldap_base_dn,
            search_filter=search_filter,
            attributes=attrs,
            size_limit=200,
        )

        results = []
        for entry in conn.entries:
            raw_email = _attr_value(entry, settings.ldap_attr_email)
            full_name = _attr_value(entry, settings.ldap_attr_full_name)
            if raw_email:
                results.append({"email": raw_email.lower(), "full_name": full_name or raw_email})

        conn.unbind()
        return results

    except LDAPSocketOpenError as exc:
        raise LDAPConnectionError(f"Cannot reach LDAP server: {exc}") from exc
    except LDAPException as exc:
        log.error("LDAP search error: %s", exc)
        return []


def _attr_value(entry, attr: str) -> str | None:
    try:
        val = entry[attr].value
        if isinstance(val, list):
            return val[0] if val else None
        return str(val) if val else None
    except Exception:
        return None


def _escape_filter(value: str) -> str:
    """Escape special LDAP filter characters per RFC 4515."""
    return (
        value
        .replace("\\", "\\5c")
        .replace("*", "\\2a")
        .replace("(", "\\28")
        .replace(")", "\\29")
        .replace("\x00", "\\00")
    )
