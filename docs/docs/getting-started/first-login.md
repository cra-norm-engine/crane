---
id: first-login
title: First Login
sidebar_position: 3
---

# First Login

After installation, complete the following steps to configure the platform for your organisation.

## 1. Sign In as Administrator

Navigate to `http://localhost:5173` (or your configured domain) and sign in using the credentials defined in your `.env` file:

- **Email**: value of `FIRST_ADMIN_EMAIL`
- **Password**: value of `FIRST_ADMIN_PASSWORD`

## 2. Change the Administrator Password

Immediately after first login, navigate to your account settings and change the administrator password to a strong, unique value. The initial password defined in `.env` is intended solely for bootstrapping purposes.

## 3. Create User Accounts

Navigate to **Settings → User Management** to create accounts for your team. Assign roles appropriate to each user's responsibilities:

| Role | Intended For |
|---|---|
| Administrator | Platform configuration, user management |
| Compliance Officer | Scope evaluations, release gate approvals, certification records |
| Cybersecurity Engineer | Risk assessments, substantial change assessment |
| Product Manager | Product registration, release management, support periods |
| Viewer | Read-only access for auditors or stakeholders |

See [User Management](/user-guide/user-management) for a full description of available roles and permissions.

## 4. Register Your First Product

Navigate to **Products** and select **New Product** to begin registering the products your organisation manufactures. At minimum, provide:

- Product code (your internal identifier)
- Product name
- Manufacturer name
- Intended use
- Product type

See [Product Registry](/user-guide/product-registry) for detailed guidance.

## 5. Run a Scope Evaluation

For each registered product, navigate to the product detail page and run a **Scope Evaluation** to determine whether the product falls within the CRA. The evaluation asks a structured series of questions and produces a documented determination with a recommended classification.

See [Scope Evaluation](/user-guide/scope-evaluation) for guidance.
