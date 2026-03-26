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

import { useAuthStore } from "@/stores/auth";

const routes: RouteRecordRaw[] = [
  {
    path: "/login",
    name: "login",
    component: LoginView,
    meta: { public: true },
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
        path: "admin/users",
        name: "admin-users",
        component: () => import("@/views/admin/AdminUsersView.vue"),
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

  if (to.meta.permissions) {
    const requiredPermissions = to.meta.permissions as string[];
    if (!authStore.hasAnyPermission(requiredPermissions)) {
      return { name: "dashboard" };
    }
  }

  return true;
});

export default router;