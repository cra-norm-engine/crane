<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Audit History</h1>
        <p class="muted">
          Choose a product, product release, or managed user and follow its full audit timeline.
        </p>
      </div>

    </div>

    <section class="card filters-card">
      <div class="filters-grid">
        <label class="field">
          <span class="field-label">Entity</span>
          <select v-model="selectedEntity" class="select" :disabled="isLoadingInstances">
            <option v-for="option in entityOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Instance</span>
          <select
            v-model="selectedInstanceId"
            class="select"
            :disabled="isLoadingInstances || instanceOptions.length === 0"
          >
            <option value="">
              {{ isLoadingInstances ? "Loading..." : "Select an instance" }}
            </option>
            <option v-for="option in instanceOptions" :key="option.id" :value="option.id">
              {{ option.label }}
            </option>
          </select>
        </label>

        <label class="field">
          <span class="field-label">Rows</span>
          <select v-model.number="resultLimit" class="select">
            <option :value="25">25</option>
            <option :value="50">50</option>
            <option :value="100">100</option>
            <option :value="150">150</option>
          </select>
        </label>
      </div>
    </section>

    <AuditTimeline
      :title="timelineTitle"
      eyebrow="Audit Workspace"
      :description="timelineDescription"
      :events="events"
      :loading="isLoadingTimeline"
      :error-message="timelineErrorMessage"
      :show-refresh="true"
      @refresh="loadTimeline"
    />
  </section>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";

import AuditTimeline from "@/components/AuditTimeline.vue";
import { adminService } from "@/services/admin-service";
import { auditService } from "@/services/audit-service";
import { productReleaseService } from "@/services/product-release-service";
import { productService } from "@/services/product-service";
import type { AdminUserRead } from "@/types/admin";
import type { AuditEventRead } from "@/types/audit";
import type { ProductSummaryRead } from "@/types/product";
import type { ProductReleaseRead } from "@/types/release-gate";

type AuditEntity = "product" | "product_release" | "user_management";

interface EntityOption {
  value: AuditEntity;
  label: string;
}

interface InstanceOption {
  id: string;
  label: string;
  subtitle?: string;
}

const entityOptions: EntityOption[] = [
  { value: "product", label: "Products" },
  { value: "product_release", label: "Product Release" },
  { value: "user_management", label: "User Management" },
];

const selectedEntity = ref<AuditEntity>("product");
const selectedInstanceId = ref("");
const resultLimit = ref(50);

const productOptions = ref<ProductSummaryRead[]>([]);
const releaseOptions = ref<ProductReleaseRead[]>([]);
const userOptions = ref<AdminUserRead[]>([]);
const events = ref<AuditEventRead[]>([]);

const isLoadingInstances = ref(false);
const isLoadingTimeline = ref(false);
const timelineErrorMessage = ref("");

const instanceOptions = computed<InstanceOption[]>(() => {
  if (selectedEntity.value === "product") {
    return productOptions.value.map((product) => ({
      id: product.id,
      label: `${product.name} (${product.product_code})`,
    }));
  }

  if (selectedEntity.value === "product_release") {
    return releaseOptions.value.map((release) => ({
      id: release.id,
      label: `Release ${release.display_version}`,
      subtitle: release.product_id,
    }));
  }

  return userOptions.value.map((user) => ({
    id: user.id,
    label: `${user.full_name} (${user.email})`,
  }));
});

const selectedInstanceLabel = computed(() => {
  return instanceOptions.value.find((option) => option.id === selectedInstanceId.value)?.label ?? "";
});

const timelineTitle = computed(() => {
  if (!selectedInstanceLabel.value) {
    return "Audit timeline";
  }

  switch (selectedEntity.value) {
    case "product":
      return selectedInstanceLabel.value;
    case "product_release":
      return `${selectedInstanceLabel.value} timeline`;
    case "user_management":
      return `${selectedInstanceLabel.value} management history`;
    default:
      return "Audit timeline";
  }
});

const timelineDescription = computed(() => {
  switch (selectedEntity.value) {
    case "product":
      return "Shows product actions plus related support period, risk assessment, security update, and evidence workflow events.";
    case "product_release":
      return "Shows release workflow, release gate, evidence review, and release-specific actions.";
    case "user_management":
      return "Shows administrative account lifecycle changes for the selected user.";
    default:
      return "";
  }
});

async function loadInstances(): Promise<void> {
  isLoadingInstances.value = true;
  selectedInstanceId.value = "";
  events.value = [];
  timelineErrorMessage.value = "";

  try {
    if (selectedEntity.value === "product") {
      productOptions.value = await productService.list();
      if (productOptions.value.length > 0) {
        selectedInstanceId.value = productOptions.value[0].id;
      }
      return;
    }

    if (selectedEntity.value === "product_release") {
      releaseOptions.value = await productReleaseService.list();
      if (releaseOptions.value.length > 0) {
        selectedInstanceId.value = releaseOptions.value[0].id;
      }
      return;
    }

    userOptions.value = await adminService.listUsers();
    if (userOptions.value.length > 0) {
      selectedInstanceId.value = userOptions.value[0].id;
    }
  } catch (error) {
    timelineErrorMessage.value =
      error instanceof Error ? error.message : "Failed to load audit entities.";
  } finally {
    isLoadingInstances.value = false;
  }
}

async function loadTimeline(): Promise<void> {
  if (!selectedInstanceId.value) {
    events.value = [];
    return;
  }

  isLoadingTimeline.value = true;
  timelineErrorMessage.value = "";

  try {
    if (selectedEntity.value === "product") {
      const response = await auditService.listEvents({
        product_id: selectedInstanceId.value,
        limit: resultLimit.value,
      });
      events.value = response.items;
      return;
    }

    if (selectedEntity.value === "product_release") {
      const response = await auditService.listEvents({
        product_release_id: selectedInstanceId.value,
        limit: resultLimit.value,
      });
      events.value = response.items;
      return;
    }

    const response = await auditService.listEvents({
      entity_id: selectedInstanceId.value,
      entity_type: "user",
      action_prefix: "admin.user.",
      limit: resultLimit.value,
    });
    events.value = response.items;
  } catch (error) {
    timelineErrorMessage.value =
      error instanceof Error ? error.message : "Failed to load audit timeline.";
  } finally {
    isLoadingTimeline.value = false;
  }
}

watch(
  selectedEntity,
  () => {
    void loadInstances();
  },
  { immediate: true },
);

watch(
  [selectedInstanceId, resultLimit],
  () => {
    void loadTimeline();
  },
);
</script>

<style scoped>
.filters-card {
  display: grid;
  gap: 1rem;
}

.filters-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 1rem;
}

.field {
  display: grid;
  gap: 0.45rem;
}

.field-label {
  font-size: 0.82rem;
  color: var(--color-text-muted);
}

.page-actions {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

@media (max-width: 960px) {
  .filters-grid {
    grid-template-columns: 1fr;
  }
}
</style>
