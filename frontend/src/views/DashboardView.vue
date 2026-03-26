<template>
  <section class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">Dashboard</h1>
        <p class="muted">
          A focused overview for CRA inventory, classification, releases, and remote processing.
        </p>
      </div>

      <div class="page-actions">
        <RouterLink class="button secondary" :to="{ name: 'products' }">
          Open inventory
        </RouterLink>
      </div>
    </div>

    <div class="grid dashboard-grid">
      <div class="card hero-card">
        <div class="hero-copy">
          <span class="badge">CRA workspace</span>
          <h2 class="hero-title">Manage products, evaluate scope, and track release readiness.</h2>
          <p class="muted">
            Start from the product inventory, then move into product-level classification,
            conformity route decisions, and remote processing review.
          </p>
        </div>

        <div class="hero-actions">
          <RouterLink class="button" :to="{ name: 'products' }">
            Go to product inventory
          </RouterLink>
        </div>
      </div>

      <div class="grid grid-3">
        <article class="card kpi-card">
          <div class="muted">Inventory</div>
          <h2 class="kpi-title">Products</h2>
          <p class="muted">
            Use the inventory page to search by product code and name, create records, and drill into
            releases and remote processing elements.
          </p>
        </article>

        <article class="card kpi-card">
          <div class="muted">Classification</div>
          <h2 class="kpi-title">Scope & class</h2>
          <p class="muted">
            Run the CRA scope wizard on each product to derive in-scope status, recommended
            classification, and suggested conformity route.
          </p>
        </article>

        <article class="card kpi-card">
          <div class="muted">Lifecycle</div>
          <h2 class="kpi-title">Releases</h2>
          <p class="muted">
            Track release versions, release status, planned dates, actual dates, and release-level
            classification snapshots.
          </p>
        </article>
      </div>

      <div class="grid dashboard-bottom">
        <div class="card">
          <div class="section-header">
            <div>
              <h2 class="section-title">What to do next</h2>
              <p class="muted">Suggested first workflow for the current implementation.</p>
            </div>
          </div>

          <ol class="workflow-list">
            <li>Create or review a product in the inventory.</li>
            <li>Open the product detail page.</li>
            <li>Run the CRA scope evaluation wizard.</li>
            <li>Add a product release and snapshot the current classification.</li>
            <li>Document remote processing elements linked to the product.</li>
          </ol>
        </div>

        <div class="card">
          <div class="section-header">
            <div>
              <h2 class="section-title">Current backend coverage</h2>
              <p class="muted">What is already wired end to end.</p>
            </div>
          </div>

          <ul class="coverage-list">
            <li>Authenticated login flow</li>
            <li>Products list and detail pages</li>
            <li>CRA scope evaluation endpoint</li>
            <li>Product releases API</li>
            <li>Remote processing elements API</li>
            <li>Audit logging for create flows</li>
          </ul>
        </div>
      </div>
    </div>
  </section>
</template>

<script setup lang="ts">
import { RouterLink } from "vue-router";
</script>

<style scoped>
.dashboard-grid {
  gap: 1rem;
}

.hero-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.hero-copy {
  max-width: 760px;
  display: grid;
  gap: 0.75rem;
}

.hero-title {
  margin: 0;
  font-size: 1.75rem;
  line-height: 1.2;
}

.hero-actions {
  display: flex;
  align-items: center;
}

.kpi-card {
  display: grid;
  gap: 0.4rem;
}

.kpi-title {
  margin: 0;
}

.dashboard-bottom {
  grid-template-columns: 1.1fr 0.9fr;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  flex-wrap: wrap;
}

.section-title {
  margin: 0;
}

.workflow-list,
.coverage-list {
  margin: 0;
  padding-left: 1.2rem;
  color: var(--color-text);
}

.workflow-list li,
.coverage-list li {
  margin: 0.5rem 0;
}

.page-actions {
  display: flex;
  gap: 0.75rem;
}

@media (max-width: 960px) {
  .dashboard-bottom {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 1.45rem;
  }
}
</style>