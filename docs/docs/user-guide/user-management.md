---
id: user-management
title: User Management
sidebar_position: 10
---

# User Management

User management covers the creation and configuration of user accounts, role assignment, and authentication. The platform supports both local (database-backed) user accounts and LDAP-based directory authentication.

## Roles and Permissions

Access to platform features is controlled through a role-based access control (RBAC) model. Each role grants a set of permissions corresponding to specific compliance workflows.

| Role | Key Permissions |
|---|---|
| **Administrator** | Full access to all features, user management, platform configuration |
| **Compliance Officer** | Scope evaluations, release gate approvals, certification records, all read access |
| **Cybersecurity Engineer** | Risk assessments, substantial change assessment, release gate evidence review |
| **Product Manager** | Product and release management, support period records, security update records |
| **Viewer** | Read-only access to all compliance records; no write permissions |

### Permission Reference

| Permission | Description |
|---|---|
| `product_read` | View products, releases, and associated records |
| `product_write` | Create and modify products and releases |
| `risk_assessment_read` | View risk assessments |
| `risk_assessment_write` | Create and modify risk assessments |
| `release_gate_read` | View release gate records |
| `release_gate_write` | Link evidence, set decisions, approve releases |
| `change_read` | View substantial change records |
| `change_write` | Create changes, conduct assessments, update compliance actions |
| `certification_read` | View certification records |
| `certification_write` | Create and modify certification records |
| `user_manage` | Create, edit, and deactivate user accounts |
| `audit_read` | Access the immutable audit event log |

## Creating a Local User Account

Navigate to **Settings → User Management** and select **New User**. Provide:

- Full name
- Email address (used as the login identifier)
- Initial password (the user should be prompted to change this on first login)
- Role assignment

## LDAP Authentication

When LDAP is enabled, users authenticate against the configured directory. Local accounts remain available as a fallback for the administrator account.

### Configuration

Set the following environment variables in `.env`:

```bash
LDAP_ENABLED=true
LDAP_SERVER=ldaps://ldap.example.com:636
LDAP_BIND_DN=cn=service-account,dc=example,dc=com
LDAP_BIND_PASSWORD=your-bind-password
LDAP_BASE_DN=ou=users,dc=example,dc=com
LDAP_USER_FILTER=(mail={username})
```

LDAP users are provisioned in the platform on first login. An administrator must assign the appropriate role to each LDAP user before they can access compliance features.

:::note
LDAP over TLS (LDAPS, port 636) is strongly recommended. Plain LDAP (port 389) transmits credentials in cleartext and must not be used in production environments.
:::

## Deactivating a User

Deactivated users cannot sign in to the platform. Their historical records (audit events, assessments authored, changes submitted) are preserved and remain attributed to their account. Deactivation does not delete any compliance records.

To deactivate a user, navigate to **Settings → User Management**, open the user record, and select **Deactivate**.

## Audit Log Access

All platform actions — including user creation, login events, and permission changes — are recorded in the immutable audit log. Audit log access requires the `audit_read` permission, which is granted to the Administrator role by default.
