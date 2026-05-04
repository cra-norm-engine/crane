import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router";

import AppLayout from "@/layouts/AppLayout.vue";
import DashboardView from "@/views/DashboardView.vue";
import LoginView from "@/views/LoginView.vue";
import NotFoundView from "@/views/NotFoundView.vue";
import ProductDetailView from "@/views/ProductDetailView.vue";
import ProductsView from "@/views/ProductsView.vue";
import RiskAssessmentsView from "@/views/RiskAssessmentsView.vue";
import RiskAssessmentDetailView from "@/views/RiskAssessmentDetailView.vue";
import AnnexMatrixView from "@/views/AnnexMatrixView.vue";
import LifecycleNotificationsView from "@/views/LifecycleNotificationsView.vue";
import SecurityUpdateHistoryView from "@/views/SecurityUpdateHistoryView.vue";
import ReleaseGateView from "@/views/ReleaseGateView.vue";
import CertificationRecordsView from "@/views/CertificationRecordsView.vue";
import SupportHubView from "@/views/SupportHubView.vue";
import ChangePasswordView from "@/views/ChangePasswordView.vue";

import VulnerabilityReportsView from "@/views/VulnerabilityReportsView.vue";
import SecurityAdvisoriesView from "@/views/SecurityAdvisoriesView.vue";
import CvdPoliciesView from "@/views/CvdPoliciesView.vue";
import SbomRecordsView from "@/views/SbomRecordsView.vue";

import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: LoginView,
    meta: { public: true },
  },
  {
    path: "/change-password",
    name: "change-password",
    component: ChangePasswordView,
  },
  {
    path: "/",
    component: AppLayout,
    children: [
      {
        path: "",
        name: "dashboard",
        component: DashboardView,
      },
      {
        path: "products",
        name: "products",
        component: ProductsView,
      },
      {
        path: "products/:productId",
        name: "product-detail",
        component: ProductDetailView,
        props: true,
      },
      {
        path: "releases/:releaseId",
        name: "release-gate",
        component: ReleaseGateView,
        props: true,
        meta: {
          permissions: ["release_read"],
        },
      },
      {
        path: "security-updates",
        name: "security-updates",
        component: SecurityUpdateHistoryView,
        meta: {
          permissions: ["security_update_read"],
        },
      },
      {
        path: "lifecycle-notifications",
        name: "lifecycle-notifications",
        component: LifecycleNotificationsView,
        meta: {
          permissions: ["lifecycle_notification_read"],
        },
      },
      {
        path: "risk-assessments",
        name: "risk-assessments",
        component: RiskAssessmentsView,
        meta: {
          permissions: ["risk_assessment_read"],
        },
      },
      {
        path: "risk-assessments/:assessmentId",
        name: "risk-assessment-detail",
        component: RiskAssessmentDetailView,
        props: true,
        meta: {
          permissions: ["risk_assessment_read"],
        },
      },
      {
        path: "annex-matrix",
        name: "annex-matrix",
        component: AnnexMatrixView,
        meta: {
          permissions: ["annex_requirement_read", "requirement_mapping_read"],
        },
      },
      {
        path: "certification-records",
        name: "certification-records",
        component: CertificationRecordsView,
        meta: {
          permissions: ["certification_record_read"],
        },
      },
      {
        path: "support-hub",
        name: "support-hub",
        component: SupportHubView,
        meta: {
          permissions: ["lifecycle_notification_read"],
        },
      },
      {
        path: "admin/users",
        name: "admin-users",
        component: () => import("@/views/admin/AdminUsersView.vue"),
        meta: {
          permissions: ["admin_manage_users"],
        },
      },
      {
        path: "admin/ldap",
        name: "admin-ldap",
        component: () => import("@/views/admin/AdminLdapView.vue"),
        meta: {
          permissions: ["admin_manage_users"],
        },
      },
      {
        path: "admin/roles",
        name: "admin-roles",
        component: () => import("@/views/admin/AdminRolesView.vue"),
        meta: {
          permissions: ["admin_manage_users"],
        },
      },
      {
        path: "changes",
        name: "changes",
        component: () => import("@/views/ChangesView.vue"),
        meta: {
          permissions: ["change_read"],
        },
      },
      {
        path: "changes/:id",
        name: "change-detail",
        component: () => import("@/views/ChangeDetailView.vue"),
        meta: {
          permissions: ["change_read"],
        },
      },
      {
        path: "audit",
        name: "audit-history",
        component: () => import("@/views/admin/AuditLogView.vue"),
        meta: {
          permissions: ["audit_read"],
        },
      },
      // Gap 6 — vulnerability lifecycle tracking (Annex I Part II §2, §5)
      {
        path: "vulnerability-reports",
        name: "vulnerability-reports",
        component: VulnerabilityReportsView,
        meta: {
          permissions: ["security_update_read"],
        },
      },
      // Gaps 3 & 7 — security advisories with embargo management (Annex I Part II §4, §8)
      {
        path: "security-advisories",
        name: "security-advisories",
        component: SecurityAdvisoriesView,
        meta: {
          permissions: ["security_update_read"],
        },
      },
      // Gap 2 — CVD policies (Annex I Part II §5)
      {
        path: "cvd-policies",
        name: "cvd-policies",
        component: CvdPoliciesView,
        meta: {
          permissions: ["security_update_read"],
        },
      },
      // Gap 10 — structured SBOM records (Annex I Part II §1)
      {
        path: "sbom-records",
        name: "sbom-records",
        component: SbomRecordsView,
        meta: {
          permissions: ["security_update_read"],
        },
      },
    ],
  },
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: NotFoundView,
    meta: { public: true },
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 };
  },
});

router.beforeEach(async (to) => {
  const authStore = useAuthStore();

  if (!authStore.isInitialized) {
    authStore.initializeFromStorage();
  }

  if (to.meta.public) {
    if (to.name === "login" && authStore.isAuthenticated) {
      return { name: "dashboard" };
    }
    return true;
  }

  if (!authStore.isAuthenticated) {
    return { name: "login", query: { redirect: to.fullPath } };
  }

  // Force local users with a temporary password to change it before proceeding.
  if (authStore.user?.must_change_password && to.name !== "change-password") {
    return { name: "change-password" };
  }

  if (to.meta.permissions) {
    const requiredPermissions = to.meta.permissions as string[];
    if (!authStore.hasAnyPermission(requiredPermissions)) {
      return { name: "dashboard" };
    }
  }

  return true;
});

export default router;
