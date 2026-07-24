<!--
  CRANE — CRA Norm Engine
  Copyright (C) 2026 Ali Mohammad Hosseini
  SPDX-License-Identifier: AGPL-3.0-or-later
  This file is part of CRANE, free software under the GNU AGPL v3.0 or later.
  See <https://www.gnu.org/licenses/>.
-->
<template>
  <section class="pi-page">

    <!-- ── Page head ── -->
    <div class="pi-head">
      <div>
        <h1 class="page-title">Product inventory</h1>
        <p class="pi-sub">Catalogue every product, decide CRA scope, track conformity readiness.</p>
      </div>
      <div class="pi-head-actions">
        <AppButton :disabled="isLoading" @click="loadProducts">
          <svg class="pi-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 12a9 9 0 1 1-3-6.7L21 8"/><path d="M21 3v5h-5"/>
          </svg>
          {{ isLoading ? 'Refreshing…' : 'Refresh' }}
        </AppButton>
        <AppButton variant="primary" @click="toggleCreateForm">
          <svg class="pi-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 5v14M5 12h14"/>
          </svg>
          {{ showCreateForm ? 'Close' : 'Add product' }}
        </AppButton>
      </div>
    </div>

    <!-- ── KPI strip — clickable scope filters ── -->
    <div class="pi-kpi-row">
      <!-- Total products -->
      <button type="button" class="pi-kpi" :class="{ 'pi-kpi-sel': !filters.scopeStatus }" @click="setScopeFilter('')">
        <div class="pi-kpi-head">
          <span>Total products</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 7l-8-4-8 4v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V7z"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val">{{ products.length }}</div>
        <div class="pi-kpi-foot">In the CRA register</div>
      </button>

      <!-- In scope -->
      <button type="button" class="pi-kpi pi-kpi-ok" :class="{ 'pi-kpi-sel': filters.scopeStatus === 'in_scope' }" @click="setScopeFilter('in_scope')">
        <div class="pi-kpi-head">
          <span>In scope</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M20 6L9 17l-5-5"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val pi-kpi-val-ok">{{ inScopeCount }}</div>
        <div class="pi-kpi-foot">CRA obligations apply</div>
      </button>

      <!-- Out of scope -->
      <button type="button" class="pi-kpi" :class="{ 'pi-kpi-sel': filters.scopeStatus === 'out_of_scope' }" @click="setScopeFilter('out_of_scope')">
        <div class="pi-kpi-head">
          <span>Out of scope</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M18 6L6 18M6 6l12 12"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val">{{ outOfScopeCount }}</div>
        <div class="pi-kpi-foot">
          <span v-if="unsignedOutOfScopeCount > 0" class="pi-pill pi-pill-warn"><span class="pi-pd"></span>{{ unsignedOutOfScopeCount }} unsigned</span>
          <span v-else class="pi-muted">justified &amp; signed</span>
        </div>
      </button>

      <!-- Critical class -->
      <div class="pi-kpi" :class="criticalCount > 0 ? 'pi-kpi-danger' : ''">
        <div class="pi-kpi-head">
          <span>Critical class</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 3l9 16H3L12 3z"/><path d="M12 10v4"/><circle cx="12" cy="17" r="0.5" fill="currentColor"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val">{{ criticalCount }}</div>
        <div class="pi-kpi-foot">
          <span v-if="criticalCount > 0" class="pi-pill pi-pill-err"><span class="pi-pd"></span>Third-party assessment</span>
          <span v-else class="pi-muted">None</span>
        </div>
      </div>

      <!-- Remote data processing -->
      <div class="pi-kpi">
        <div class="pi-kpi-head">
          <span>Remote data</span>
          <span class="pi-kpi-ic">
            <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 2a9 9 0 0 0 0 18M12 2a9 9 0 0 1 0 18M3 12h18M12 2v20"/>
            </svg>
          </span>
        </div>
        <div class="pi-kpi-val">{{ remoteProcessingCount }}</div>
        <div class="pi-kpi-foot">Rely on a remote service</div>
      </div>
    </div>

    <!-- ── Filter toolbar — search + a single Filters popover + Sort ──
         Progressive disclosure: the seven category filters live inside one
         popover instead of a wall of always-visible pills. Any active filter
         surfaces below as a removable chip, so the current query stays visible
         without cluttering the toolbar. -->
    <div class="pi-toolbar">
      <!-- Search -->
      <div class="pi-filter-search">
        <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
          <circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>
        </svg>
        <input v-model.trim="filters.search" placeholder="Search by product code, name, manufacturer…" />
      </div>

      <!-- Filters popover trigger -->
      <div class="pi-pop-wrap">
        <button
          type="button"
          class="pi-tbtn"
          :class="{ 'pi-tbtn-active': activeFilterCount > 0 }"
          :aria-expanded="showFilterMenu"
          @click="showFilterMenu = !showFilterMenu"
        >
          <svg class="pi-ico-sm" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
            <path d="M4 5h16M7 12h10M10 19h4"/>
          </svg>
          Filters
          <span v-if="activeFilterCount > 0" class="pi-tbtn-count">{{ activeFilterCount }}</span>
          <svg class="pi-fpill-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </button>

        <!-- Popover menu -->
        <div v-if="showFilterMenu" class="pi-pop-backdrop" @click="showFilterMenu = false"></div>
        <div v-if="showFilterMenu" class="pi-pop-menu" role="dialog" aria-label="Filters">
          <div class="pi-pop-head">
            <span>Filters</span>
            <button v-if="activeFilterCount > 0" type="button" class="pi-pop-clear" @click="resetFilters">Clear all</button>
          </div>

          <label class="pi-pop-field">
            <span>Scope</span>
            <select v-model="filters.scopeStatus" class="pi-select">
              <option value="">All</option>
              <option value="in_scope">In scope</option>
              <option value="out_of_scope">Out of scope</option>
              <option value="undecided">Undecided</option>
            </select>
          </label>

          <label class="pi-pop-field">
            <span>Classification</span>
            <select v-model="filters.classification" class="pi-select">
              <option value="">All</option>
              <option value="normal">Default</option>
              <option value="important_class_1">Important Class I</option>
              <option value="important_class_2">Important Class II</option>
              <option value="critical">Critical</option>
              <option value="foss">FOSS</option>
            </select>
          </label>

          <label class="pi-pop-field">
            <span>Lifecycle</span>
            <select v-model="filters.lifecycleStatus" class="pi-select">
              <option value="">All</option>
              <option value="active">Active</option>
              <option value="legacy">Legacy</option>
            </select>
          </label>

          <label class="pi-pop-field">
            <span>CRA type</span>
            <select v-model="filters.productType" class="pi-select">
              <option value="">All</option>
              <option value="type1_software">SW — software only</option>
              <option value="type2_hardware_with_digital">SW + HW — hardware with digital</option>
              <option value="undecided">Untyped</option>
            </select>
          </label>

          <label class="pi-pop-field">
            <span>Conformity route</span>
            <select v-model="filters.conformityRoute" class="pi-select">
              <option value="">All</option>
              <option value="self_assessment">Self-assessment</option>
              <option value="third_party_assessment">Third-party</option>
              <option value="not_applicable">N/A</option>
              <option value="undecided">Undecided</option>
            </select>
          </label>

          <label class="pi-pop-field">
            <span>Support</span>
            <select v-model="filters.supportStatus" class="pi-select">
              <option value="">All</option>
              <option value="set">Support set</option>
              <option value="missing">Not set</option>
              <option value="active">Active</option>
              <option value="approaching_eos">Approaching EOS</option>
              <option value="expired">Expired</option>
            </select>
          </label>

          <label class="pi-pop-field">
            <span>Updated</span>
            <select v-model="filters.updatedWithin" class="pi-select">
              <option value="">Any time</option>
              <option value="7">Last 7 days</option>
              <option value="30">Last 30 days</option>
              <option value="90">Last 90 days</option>
            </select>
          </label>

          <div class="pi-pop-foot">
            <AppButton variant="primary" @click="showFilterMenu = false">Done</AppButton>
          </div>
        </div>
      </div>

      <!-- Sort -->
      <div class="pi-pop-wrap pi-sort-group">
        <div class="pi-fpill-wrap">
          <span class="pi-fpill-lbl">Sort: <strong>{{ sortLabel }}</strong></span>
          <svg class="pi-fpill-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 9l6 6 6-6"/>
          </svg>
          <select v-model="filters.sortBy" class="pi-fpill-select" aria-label="Sort by">
            <option value="updated_desc">Latest updated</option>
            <option value="updated_asc">Oldest updated</option>
            <option value="name_asc">Name A–Z</option>
            <option value="name_desc">Name Z–A</option>
            <option value="code_asc">Code A–Z</option>
            <option value="code_desc">Code Z–A</option>
            <option value="support_end_asc">Support end ↑</option>
            <option value="support_end_desc">Support end ↓</option>
          </select>
        </div>
      </div>
    </div>

    <!-- ── Active-filter chip row — one removable chip per active filter ── -->
    <div v-if="activeFilterChips.length" class="pi-chip-row">
      <button
        v-for="chip in activeFilterChips"
        :key="chip.key"
        type="button"
        class="pi-chip"
        @click="chip.clear()"
      >
        <span class="pi-chip-k">{{ chip.label }}:</span>
        <span class="pi-chip-v">{{ chip.value }}</span>
        <svg class="pi-chip-x" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M6 6l12 12M6 18L18 6"/>
        </svg>
      </button>
      <button type="button" class="pi-chip-clear" @click="resetFilters">Clear all</button>
    </div>

    <!-- ── Create form panel ── -->
    <div v-if="showCreateForm" class="pi-panel pi-form-panel">
      <div class="pi-form-head">
        <div>
          <h3 class="pi-form-title">Create product</h3>
          <p class="pi-muted pi-form-sub">Add a new product to the CRA inventory.</p>
        </div>
      </div>

      <form class="pi-form-grid" @submit.prevent="createProduct">
        <label class="pi-field">
          <span class="pi-field-lbl">Product code</span>
          <input v-model.trim="form.product_code" class="pi-input" required maxlength="100" />
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Name</span>
          <input v-model.trim="form.name" class="pi-input" required maxlength="255" />
        </label>

        <label class="pi-field pi-field-span2">
          <span class="pi-field-lbl">Description</span>
          <textarea v-model.trim="form.description" class="pi-textarea" rows="3" />
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Manufacturer name</span>
          <input v-model.trim="form.manufacturer_name" class="pi-input" required maxlength="255" />
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Product type</span>
          <input v-model.trim="form.product_type" class="pi-input" required maxlength="150" />
        </label>

        <label class="pi-field pi-field-span2">
          <span class="pi-field-lbl">Intended use</span>
          <textarea v-model.trim="form.intended_use" class="pi-textarea" rows="3" required />
        </label>

        <!-- Parent product picker -->
        <div class="pi-field pi-field-span2">
          <span class="pi-field-lbl">
            Parent product
            <span class="pi-field-hint">(optional — set if this is a variant or sub-product)</span>
          </span>
          <div class="pi-parent-picker">
            <button type="button" class="pi-input pi-parent-trigger" @click="showParentPicker = true">
              <span v-if="form.parent_product_id && selectedParentProduct">
                {{ selectedParentProduct.product_code }} — {{ selectedParentProduct.name }}
              </span>
              <span v-else class="pi-muted">None — top-level product</span>
            </button>
            <button v-if="form.parent_product_id" type="button" class="pi-parent-clear" @click="form.parent_product_id = null" title="Clear parent">✕</button>
          </div>
        </div>

        <label class="pi-field">
          <span class="pi-field-lbl">Classification</span>
          <select v-model="form.current_classification" class="pi-select">
            <option value="normal">Default</option>
            <option value="important_class_1">Important Class I</option>
            <option value="important_class_2">Important Class II</option>
            <option value="critical">Critical</option>
            <option value="foss">FOSS</option>
          </select>
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Scope status</span>
          <select v-model="form.scope_status" class="pi-select">
            <option value="undecided">Undecided</option>
            <option value="in_scope">In scope</option>
            <option value="out_of_scope">Out of scope</option>
          </select>
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Lifecycle</span>
          <select v-model="form.lifecycle_status" class="pi-select">
            <option value="active">Active — full obligations when in scope</option>
            <option value="legacy">Legacy — reporting-only when in scope</option>
          </select>
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">CRA product type</span>
          <select v-model="form.product_type_class" class="pi-select">
            <option value="undecided">Undecided</option>
            <option value="type1_software">SW — software only</option>
            <option value="type2_hardware_with_digital">SW + HW — hardware with digital elements</option>
          </select>
        </label>

        <label class="pi-field">
          <span class="pi-field-lbl">Conformity route</span>
          <select v-model="form.conformity_route" class="pi-select">
            <option value="undecided">Undecided</option>
            <option value="self_assessment">Self-assessment</option>
            <option value="third_party_assessment">Third-party</option>
            <option value="not_applicable">Not applicable</option>
          </select>
        </label>

        <!-- Gap 2 — embedded product flag: enables per-release HW+SW version fields -->
        <label class="pi-field pi-field-span2 pi-field-checkbox">
          <input type="checkbox" v-model="form.is_embedded_product" />
          <span>
            <strong>Embedded product (hardware + software/firmware)</strong>
            <span class="pi-field-hint"> — enables separate hardware and software version fields on each release</span>
          </span>
        </label>

        <div class="pi-form-actions pi-field-span2">
          <p v-if="formError" class="pi-form-error">{{ formError }}</p>
          <AppButton variant="primary" type="submit" :disabled="isSubmitting">
            {{ isSubmitting ? 'Saving…' : 'Create product' }}
          </AppButton>
        </div>
      </form>
    </div>

    <!-- ── Inventory panel ── -->
    <div class="pi-panel">
      <div class="pi-panel-head">
        <h3 class="pi-panel-title">
          Inventory
          <span class="pi-count-pill">{{ filteredProducts.length }} results</span>
        </h3>
      </div>

      <!-- States -->
      <div v-if="errorMessage" class="pi-state pi-state-err">{{ errorMessage }}</div>

      <!-- Skeleton loader — mirrors the table shape so the layout doesn't jump. -->
      <div v-else-if="isLoading" class="pi-skel-wrap" aria-hidden="true">
        <div v-for="n in 6" :key="n" class="pi-skel-row">
          <span class="pi-skel pi-skel-mark"></span>
          <span class="pi-skel pi-skel-line pi-skel-w40"></span>
          <span class="pi-skel pi-skel-pill"></span>
          <span class="pi-skel pi-skel-pill"></span>
          <span class="pi-skel pi-skel-pill"></span>
          <span class="pi-skel pi-skel-line pi-skel-w20"></span>
        </div>
      </div>

      <!-- Empty: no products at all vs. filtered-to-nothing get different guidance. -->
      <div v-else-if="filteredProducts.length === 0" class="pi-empty">
        <div class="pi-empty-ic">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="width:30px;height:30px">
            <path d="M20 7l-8-4-8 4v6c0 5 3.5 7.5 8 9 4.5-1.5 8-4 8-9V7z"/><path d="M9 12l2 2 4-4"/>
          </svg>
        </div>
        <template v-if="activeFilterCount > 0 || filters.search">
          <h4 class="pi-empty-title">No products match your filters</h4>
          <p class="pi-empty-sub">Try widening or clearing the active filters to see more of the register.</p>
          <AppButton @click="resetFilters">Clear filters</AppButton>
        </template>
        <template v-else>
          <h4 class="pi-empty-title">Your CRA register is empty</h4>
          <p class="pi-empty-sub">Add your first product to start cataloguing scope decisions, conformity routes and support periods.</p>
          <AppButton variant="primary" @click="toggleCreateForm">
            <svg class="pi-ico" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
              <path d="M12 5v14M5 12h14"/>
            </svg>
            Add your first product
          </AppButton>
        </template>
      </div>

      <div v-else class="pi-table-wrap">
        <table class="pi-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Code</th>
              <th>Type</th>
              <th>Class</th>
              <th>Scope</th>
              <th>Obligation</th>
              <th>Route</th>
              <th>Flags</th>
              <th>Support</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="product in filteredProducts"
              :key="product.id"
              class="pi-row"
              :class="{ 'pi-row-flagged': product.current_classification === 'critical', 'pi-row-active': product.id === drawerProductId }"
              @click="openDrawer(product.id)"
            >
              <!-- Product cell: initials mark + name + sub -->
              <td>
                <div class="pi-prod-cell">
                  <div
                    class="pi-prod-mark"
                    :class="{ 'pi-prod-mark-danger': product.current_classification === 'critical' }"
                  >{{ productInitials(product.name) }}</div>
                  <div>
                    <div class="pi-prod-name">{{ product.name }}</div>
                    <div class="pi-prod-sub">{{ product.manufacturer_name }}</div>
                  </div>
                </div>
              </td>
              <td><span class="pi-mono">{{ product.product_code }}</span></td>
              <!-- Typed CRA product classification -->
              <td>
                <span class="pi-pill" :class="productTypePillClass(product.product_type_class)">
                  {{ formatProductType(product.product_type_class) }}
                </span>
              </td>
              <!-- Classification -->
              <td>
                <span class="pi-pill" :class="classificationPillClass(product.current_classification)">
                  <span class="pi-pd"></span>{{ formatClassification(product.current_classification) }}
                </span>
              </td>
              <!-- Scope -->
              <td>
                <span class="pi-pill" :class="scopePillClass(product.scope_status)">
                  <span class="pi-pd"></span>{{ formatScopeStatus(product.scope_status) }}
                </span>
              </td>
              <!-- Obligation — derived from scope + lifecycle (not an independent axis) -->
              <td>
                <span
                  class="pi-pill"
                  :class="obligationView(product.scope_status, product.lifecycle_status).pillClass"
                  :title="obligationView(product.scope_status, product.lifecycle_status).hint"
                >
                  <span class="pi-pd"></span>{{ obligationView(product.scope_status, product.lifecycle_status).label }}
                </span>
              </td>
              <!-- Conformity route -->
              <td>
                <span class="pi-pill" :class="conformityRoutePillClass(product.conformity_route)">
                  {{ formatConformityRoute(product.conformity_route) }}
                </span>
              </td>
              <!-- Flags -->
              <td>
                <div class="pi-flags">
                  <span
                    v-for="flag in productFlags(product)"
                    :key="flag.key"
                    class="pi-flag"
                    :class="flag.variant"
                    :title="flag.title"
                  >{{ flag.label }}</span>
                  <span v-if="productFlags(product).length === 0" class="pi-flags-empty">—</span>
                </div>
              </td>
              <!-- Support period -->
              <td>
                <template v-if="supportByProductId[product.id]">
                  <span class="pi-pill" :class="supportPillClass(getSupportStatus(product.id))">
                    <span class="pi-pd"></span>{{ formatSupportStatus(getSupportStatus(product.id)) }}
                  </span>
                </template>
                <template v-else>
                  <span class="pi-muted pi-support-none">Not set</span>
                </template>
              </td>
              <!-- Action -->
              <td class="pi-action-cell">
                <svg class="pi-row-chev" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M9 6l6 6-6 6"/>
                </svg>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pi-panel-foot">
        <span>
          Showing <strong>{{ filteredProducts.length }}</strong> of <strong>{{ products.length }}</strong> products
        </span>
        <!-- Flag legend — defines every chip shown in the Flags column -->
        <div class="pi-legend">
          <span class="pi-legend-item"><span class="pi-flag pi-flag-violet">S</span> System</span>
          <span class="pi-legend-item"><span class="pi-flag pi-flag-cyan">T</span> Tailor-made</span>
          <span class="pi-legend-item"><span class="pi-flag pi-flag-green">R</span> Remote data</span>
          <span class="pi-legend-item"><span class="pi-flag pi-flag-blue">E</span> Embedded</span>
          <span class="pi-legend-item"><span class="pi-flag pi-flag-amber">P</span> Pre-CRA</span>
          <span class="pi-legend-item"><span class="pi-flag pi-flag-danger">⚠</span> Unsigned</span>
        </div>
      </div>
    </div>

    <!-- ── Right-side detail drawer ── -->
    <Teleport to="body">
      <div v-if="drawerProductId" class="pi-drawer-scrim" @click="closeDrawer"></div>
      <aside v-if="drawerProductId" class="pi-drawer" role="dialog" aria-modal="true" aria-label="Product detail">
        <!-- Drawer header -->
        <div class="pi-drawer-head">
          <div class="pi-drawer-head-main">
            <span class="pi-mono pi-drawer-code">{{ drawerProduct?.product_code ?? '' }}</span>
            <h3 class="pi-drawer-title">{{ drawerProduct?.name ?? 'Loading…' }}</h3>
            <div v-if="drawerProduct" class="pi-drawer-badges">
              <span class="pi-pill" :class="scopePillClass(drawerProduct.scope_status)">
                <span class="pi-pd"></span>{{ formatScopeStatus(drawerProduct.scope_status) }}
              </span>
              <span class="pi-pill" :class="classificationPillClass(drawerProduct.current_classification)">
                <span class="pi-pd"></span>{{ formatClassification(drawerProduct.current_classification) }}
              </span>
              <span class="pi-pill" :class="productTypePillClass(drawerProduct.product_type_class)">
                {{ formatProductType(drawerProduct.product_type_class) }}
              </span>
            </div>
          </div>
          <button type="button" class="pi-drawer-close" aria-label="Close" @click="closeDrawer">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" style="width:17px;height:17px">
              <path d="M6 6l12 12M6 18L18 6"/>
            </svg>
          </button>
        </div>

        <!-- Drawer body -->
        <div class="pi-drawer-body">
          <div v-if="drawerLoading" class="pi-state">Loading product…</div>
          <div v-else-if="drawerError" class="pi-state pi-state-err">{{ drawerError }}</div>

          <template v-else-if="drawerProduct">
            <!-- Flags -->
            <div v-if="productFlags(drawerProduct).length" class="pi-drawer-flagrow">
              <div
                v-for="flag in productFlags(drawerProduct)"
                :key="flag.key"
                class="pi-flag-line"
              >
                <span class="pi-flag" :class="flag.variant">{{ flag.label }}</span>
                <span class="pi-flag-txt">{{ flag.title }}</span>
              </div>
            </div>

            <!-- Attributes -->
            <section class="pi-drawer-sec">
              <h4 class="pi-drawer-sec-title">Product attributes</h4>
              <dl class="pi-kv">
                <div class="pi-kv-row"><dt>Manufacturer</dt><dd>{{ drawerProduct.manufacturer_name }}</dd></div>
                <div class="pi-kv-row"><dt>Product type</dt><dd>{{ drawerProduct.product_type }}</dd></div>
                <div class="pi-kv-row"><dt>CRA type</dt><dd>{{ formatProductType(drawerProduct.product_type_class) }}</dd></div>
                <div class="pi-kv-row"><dt>Lifecycle</dt><dd :title="lifecycleHint(drawerProduct.lifecycle_status)">{{ formatLifecycle(drawerProduct.lifecycle_status) }}</dd></div>
                <div class="pi-kv-row">
                  <dt>Obligation</dt>
                  <dd>
                    <span
                      class="pi-pill"
                      :class="obligationView(drawerProduct.scope_status, drawerProduct.lifecycle_status).pillClass"
                      :title="obligationView(drawerProduct.scope_status, drawerProduct.lifecycle_status).hint"
                    ><span class="pi-pd"></span>{{ obligationView(drawerProduct.scope_status, drawerProduct.lifecycle_status).label }}</span>
                  </dd>
                </div>
                <div class="pi-kv-row"><dt>Conformity route</dt><dd>{{ formatConformityRoute(drawerProduct.conformity_route) }}</dd></div>
                <div class="pi-kv-row"><dt>Placed on market</dt><dd>{{ formatDate(drawerProduct.first_placed_on_market_date) }}</dd></div>
                <div class="pi-kv-row"><dt>Intended use</dt><dd class="pi-kv-long">{{ drawerProduct.intended_use }}</dd></div>
              </dl>
            </section>

            <!-- Scope decision -->
            <section class="pi-drawer-sec">
              <h4 class="pi-drawer-sec-title">
                {{ drawerProduct.scope_status === 'out_of_scope' ? 'Out-of-scope decision' : 'Scope decision' }}
              </h4>
              <div
                class="pi-scope-box"
                :class="drawerProduct.scope_status === 'out_of_scope' ? 'pi-scope-box-out' : 'pi-scope-box-in'"
              >
                <template v-if="drawerProduct.scope_status === 'undecided'">
                  <p class="pi-muted pi-scope-empty">Scope not yet decided — run the scope wizard on the product page.</p>
                </template>
                <template v-else>
                  <dl class="pi-kv">
                    <div v-if="drawerProduct.out_of_scope_justification" class="pi-kv-row">
                      <dt>Justification</dt><dd class="pi-kv-long">{{ drawerProduct.out_of_scope_justification }}</dd>
                    </div>
                    <div class="pi-kv-row">
                      <dt>Decided by</dt>
                      <dd>{{ drawerProduct.scope_decided_by_name ?? '—' }}
                        <span v-if="drawerProduct.scope_decided_at" class="pi-muted"> · {{ formatDate(drawerProduct.scope_decided_at) }}</span>
                      </dd>
                    </div>
                    <div class="pi-kv-row">
                      <dt>Signature</dt>
                      <dd>
                        <span v-if="drawerProduct.scope_decision_signature">{{ drawerProduct.scope_decision_signature }}</span>
                        <span v-else class="pi-pill pi-pill-warn"><span class="pi-pd"></span>Unsigned</span>
                      </dd>
                    </div>
                  </dl>
                </template>
              </div>
            </section>

            <!-- System profile -->
            <section v-if="drawerProduct.system_profile_json" class="pi-drawer-sec">
              <h4 class="pi-drawer-sec-title">System profile <span class="pi-sec-note">· sold as a system</span></h4>
              <dl class="pi-kv">
                <div class="pi-kv-row"><dt>Sold as a product</dt><dd>{{ formatBool(drawerProduct.system_profile_json.sold_as_product) }}</dd></div>
                <div class="pi-kv-row"><dt>Marketed as a product</dt><dd>{{ formatBool(drawerProduct.system_profile_json.marketed_as_product) }}</dd></div>
                <div class="pi-kv-row"><dt>Who integrates</dt><dd>{{ drawerProduct.system_profile_json.who_integrates_system ?? '—' }}</dd></div>
                <div class="pi-kv-row"><dt>Core combination</dt><dd class="pi-kv-long">{{ drawerProduct.system_profile_json.core_minimum_products_combination ?? '—' }}</dd></div>
              </dl>
            </section>

            <!-- Tailor-made terms -->
            <section v-if="drawerProduct.tailor_made_terms_json" class="pi-drawer-sec">
              <h4 class="pi-drawer-sec-title">Tailor-made terms <span class="pi-sec-note">· custom B2B contract</span></h4>
              <dl class="pi-kv">
                <div class="pi-kv-row"><dt>Specific user</dt><dd>{{ drawerProduct.tailor_made_terms_json.specific_user ?? '—' }}</dd></div>
                <div class="pi-kv-row"><dt>Support period</dt><dd>{{ drawerProduct.tailor_made_terms_json.customized_support_period ?? '—' }}</dd></div>
                <div class="pi-kv-row"><dt>Security config</dt><dd class="pi-kv-long">{{ drawerProduct.tailor_made_terms_json.customized_security_config ?? '—' }}</dd></div>
                <div class="pi-kv-row"><dt>Agreement</dt><dd class="pi-kv-long">{{ drawerProduct.tailor_made_terms_json.agreement_via_contractual_terms ?? '—' }}</dd></div>
              </dl>
            </section>

            <!-- Remote processing elements -->
            <section v-if="drawerProduct.remote_processing_elements.length" class="pi-drawer-sec">
              <h4 class="pi-drawer-sec-title">Remote data processing <span class="pi-sec-note">· relies on</span></h4>
              <div class="pi-rdps-list">
                <div v-for="rpe in drawerProduct.remote_processing_elements" :key="rpe.id" class="pi-rdps-item">
                  <div class="pi-rdps-name">{{ rpe.name }}</div>
                  <div class="pi-rdps-meta">
                    <span v-if="rpe.provider_name">{{ rpe.provider_name }}</span>
                    <span v-if="rpe.geographic_location"> · {{ rpe.geographic_location }}</span>
                  </div>
                </div>
              </div>
            </section>
          </template>
        </div>

        <!-- Drawer footer -->
        <div v-if="drawerProduct" class="pi-drawer-foot">
          <!-- Delete confirmation panel — type the product code to confirm -->
          <div v-if="deleteConfirmOpen" class="pi-del-confirm">
            <p class="pi-del-warn">
              This permanently deletes <strong>{{ drawerProduct.name }}</strong> and all its releases,
              assessments and related records. This cannot be undone.
            </p>
            <label class="pi-del-label">
              Type <span class="pi-mono">{{ drawerProduct.product_code }}</span> to confirm
            </label>
            <input
              v-model.trim="deleteConfirmCode"
              class="pi-input pi-del-input"
              :placeholder="drawerProduct.product_code"
              @keyup.enter="deleteProduct"
            />
            <div class="pi-del-actions">
              <AppButton
                variant="danger"
                :disabled="isDeleting || deleteConfirmCode !== drawerProduct.product_code"
                @click="deleteProduct"
              >
                {{ isDeleting ? 'Deleting…' : 'Delete product' }}
              </AppButton>
              <AppButton :disabled="isDeleting" @click="resetDeleteConfirm">Cancel</AppButton>
            </div>
          </div>

          <!-- Default footer actions -->
          <template v-else>
            <AppButton variant="primary" @click="openProduct(drawerProduct.id)">Open full page</AppButton>
            <button type="button" class="pi-del-trigger" @click="deleteConfirmOpen = true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" style="width:14px;height:14px">
                <path d="M3 6h18M8 6V4h8v2M19 6l-1 14H6L5 6"/>
              </svg>
              Delete
            </button>
            <AppButton @click="closeDrawer">Close</AppButton>
          </template>
        </div>
      </aside>
    </Teleport>

    <!-- ── Parent product picker modal ── -->
    <Teleport to="body">
      <div v-if="showParentPicker" class="pi-picker-backdrop" @click.self="showParentPicker = false">
        <div class="pi-picker-modal" role="dialog" aria-modal="true" aria-label="Select parent product">
          <div class="pi-picker-head">
            <h3 class="pi-picker-title">Select parent product</h3>
            <button type="button" class="pi-picker-close" @click="showParentPicker = false">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" style="width:16px;height:16px">
                <path d="M6 6l12 12M6 18L18 6"/>
              </svg>
            </button>
          </div>
          <input
            v-model="parentPickerSearch"
            class="pi-input"
            type="search"
            placeholder="Search by code, name or manufacturer…"
            autofocus
          />
          <div class="pi-picker-list">
            <p v-if="filteredParentProducts.length === 0" class="pi-muted pi-picker-empty">
              No products match your search.
            </p>
            <button
              v-for="product in filteredParentProducts"
              :key="product.id"
              type="button"
              class="pi-picker-item"
              :class="{ 'pi-picker-item-sel': form.parent_product_id === product.id }"
              @click="selectParent(product.id)"
            >
              <div class="pi-picker-item-row">
                <span class="pi-picker-code">{{ product.product_code }}</span>
                <span class="pi-picker-name">{{ product.name }}</span>
              </div>
              <div class="pi-muted pi-picker-mfr">{{ product.manufacturer_name }}</div>
            </button>
          </div>
        </div>
      </div>
    </Teleport>

  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";

import AppButton from "@/components/AppButton.vue";
import { productService } from "@/services/product-service";
import { supportPeriodService } from "@/services/support-period-service";
import type {
  ConformityRoute,
  ProductClassification,
  ProductCreate,
  ProductDetailRead,
  ProductLifecycleStatus,
  ProductSummaryRead,
  ProductType,
  ScopeStatus,
  SupportPeriodRecordRead,
} from "@/types/product";

const router = useRouter();

const products = ref<ProductSummaryRead[]>([]);
const supportByProductId = ref<Record<string, SupportPeriodRecordRead | null>>({});
const isLoading = ref(false);
const isSubmitting = ref(false);
const errorMessage = ref("");
const formError = ref("");
const showCreateForm = ref(false);
const showFilterMenu = ref(false);
const showParentPicker = ref(false);
const parentPickerSearch = ref("");

// ── Right-side detail drawer ──
// Opens on row click with the full product detail (fetched lazily). Keeps the
// user in the inventory context; "Open full page" still routes to the detail view.
const drawerProductId = ref<string | null>(null);
const drawerProduct = ref<ProductDetailRead | null>(null);
const drawerLoading = ref(false);
const drawerError = ref("");
// Delete flow — a two-step confirm (type the product code) guards the cascade
// delete of a product and all its releases, assessments, and related records.
const deleteConfirmOpen = ref(false);
const deleteConfirmCode = ref("");
const isDeleting = ref(false);

const filters = reactive({
  search: "",
  scopeStatus: "" as ScopeStatus | "",
  classification: "" as ProductClassification | "",
  lifecycleStatus: "" as ProductLifecycleStatus | "",
  productType: "" as ProductType | "",
  conformityRoute: "" as ConformityRoute | "",
  supportStatus: "" as "" | "set" | "missing" | "active" | "approaching_eos" | "expired",
  updatedWithin: "",
  sortBy: "updated_desc",
});

const form = reactive<ProductCreate>({
  product_code: "",
  name: "",
  description: null,
  parent_product_id: null,
  manufacturer_name: "",
  intended_use: "",
  product_type: "",
  current_classification: "normal",
  scope_status: "undecided",
  lifecycle_status: "active",
  product_type_class: "undecided",
  conformity_route: "undecided",
  is_embedded_product: false,
});

/** Returns 2-letter initials for the product name. */
function productInitials(name: string): string {
  const words = name.trim().split(/\s+/);
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

/** The product object currently selected as parent (used to display its name in the trigger button). */
const selectedParentProduct = computed(() =>
  form.parent_product_id
    ? products.value.find((p) => p.id === form.parent_product_id) ?? null
    : null,
);

/** Products shown inside the picker popup, filtered by the picker's own search input. */
const filteredParentProducts = computed(() => {
  const q = parentPickerSearch.value.trim().toLowerCase();
  if (!q) return products.value;
  return products.value.filter(
    (p) =>
      p.product_code.toLowerCase().includes(q) ||
      p.name.toLowerCase().includes(q) ||
      p.manufacturer_name.toLowerCase().includes(q),
  );
});

/** Human-readable label for the current sort value (shown in the sort pill). */
const sortLabel = computed(() => {
  const map: Record<string, string> = {
    updated_desc: "Latest updated",
    updated_asc:  "Oldest updated",
    name_asc:     "Name A–Z",
    name_desc:    "Name Z–A",
    code_asc:     "Code A–Z",
    code_desc:    "Code Z–A",
    support_end_asc:  "Support end ↑",
    support_end_desc: "Support end ↓",
  };
  return map[filters.sortBy] ?? "Latest updated";
});

function selectParent(productId: string): void {
  form.parent_product_id = productId;
  showParentPicker.value = false;
  parentPickerSearch.value = "";
}

const filteredProducts = computed(() => {
  const query = filters.search.trim().toLowerCase();
  const updatedWithinDays = filters.updatedWithin ? Number(filters.updatedWithin) : null;
  const now = Date.now();

  const filtered = products.value.filter((product) => {
    const supportRecord = supportByProductId.value[product.id] ?? null;
    const supportStatus = getSupportStatus(product.id);

    const matchesSearch = !query
      ? true
      : [
          product.product_code,
          product.name,
          product.manufacturer_name,
          product.product_type,
          supportRecord?.support_type ?? "",
          supportRecord?.support_end_date ?? "",
        ]
          .join(" ")
          .toLowerCase()
          .includes(query);

    const matchesScope = !filters.scopeStatus || product.scope_status === filters.scopeStatus;
    const matchesClassification =
      !filters.classification || product.current_classification === filters.classification;
    const matchesLifecycle =
      !filters.lifecycleStatus || product.lifecycle_status === filters.lifecycleStatus;
    const matchesProductType =
      !filters.productType || product.product_type_class === filters.productType;
    const matchesConformityRoute =
      !filters.conformityRoute || product.conformity_route === filters.conformityRoute;

    const matchesSupportStatus =
      !filters.supportStatus ||
      (filters.supportStatus === "set" && Boolean(supportRecord)) ||
      (filters.supportStatus === "missing" && !supportRecord) ||
      (filters.supportStatus === "active" && supportStatus === "active") ||
      (filters.supportStatus === "approaching_eos" && supportStatus === "approaching_eos") ||
      (filters.supportStatus === "expired" && supportStatus === "expired");

    const matchesUpdated = !updatedWithinDays
      ? true
      : now - new Date(product.updated_at).getTime() <= updatedWithinDays * 24 * 60 * 60 * 1000;

    return matchesSearch && matchesScope && matchesClassification && matchesLifecycle && matchesProductType && matchesConformityRoute && matchesSupportStatus && matchesUpdated;
  });

  return [...filtered].sort((a, b) => {
    switch (filters.sortBy) {
      case "updated_asc":
        return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime();
      case "name_asc":
        return a.name.localeCompare(b.name);
      case "name_desc":
        return b.name.localeCompare(a.name);
      case "code_asc":
        return a.product_code.localeCompare(b.product_code);
      case "code_desc":
        return b.product_code.localeCompare(a.product_code);
      case "support_end_asc":
        return supportEndTimestamp(a.id) - supportEndTimestamp(b.id);
      case "support_end_desc":
        return supportEndTimestamp(b.id) - supportEndTimestamp(a.id);
      case "updated_desc":
      default:
        return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
    }
  });
});

const inScopeCount = computed(() =>
  products.value.filter((product) => product.scope_status === "in_scope").length,
);

const criticalCount = computed(() =>
  products.value.filter((product) => product.current_classification === "critical").length,
);

function supportEndTimestamp(productId: string): number {
  const support = supportByProductId.value[productId];
  if (!support?.support_end_date) return Number.MAX_SAFE_INTEGER;
  return new Date(support.support_end_date).getTime();
}

function getSupportStatus(productId: string): "not_set" | "active" | "approaching_eos" | "expired" {
  const support = supportByProductId.value[productId];
  if (!support) return "not_set";

  const endDate = new Date(`${support.support_end_date}T00:00:00`);
  const now = new Date();
  const sixMonthsFromNow = new Date();
  sixMonthsFromNow.setMonth(sixMonthsFromNow.getMonth() + 6);

  if (endDate.getTime() < now.getTime()) return "expired";
  if (endDate.getTime() <= sixMonthsFromNow.getTime()) return "approaching_eos";
  return "active";
}

function formatSupportStatus(value: "not_set" | "active" | "approaching_eos" | "expired"): string {
  switch (value) {
    case "active":         return "Active";
    case "approaching_eos": return "Approaching EOS";
    case "expired":        return "Expired";
    default:               return "Not set";
  }
}

function supportPillClass(value: "not_set" | "active" | "approaching_eos" | "expired"): string {
  switch (value) {
    case "active":          return "pi-pill-ok";
    case "approaching_eos": return "pi-pill-warn";
    case "expired":         return "pi-pill-err";
    default:                return "pi-pill-flat";
  }
}

/** Label for the Support *filter* values (a superset of the derived statuses). */
function formatSupportFilter(value: string): string {
  switch (value) {
    case "set":     return "Support set";
    case "missing": return "Not set";
    default:        return formatSupportStatus(value as "not_set" | "active" | "approaching_eos" | "expired");
  }
}

function formatClassification(value: ProductClassification | string): string {
  switch (value) {
    case "important_class_1": return "Important Class I";
    case "important_class_2": return "Important Class II";
    case "critical":          return "Critical";
    case "foss":              return "FOSS";
    default:                  return "Default";
  }
}

function formatScopeStatus(value: ScopeStatus | string): string {
  switch (value) {
    case "in_scope":    return "In scope";
    case "out_of_scope": return "Out of scope";
    default:            return "Undecided";
  }
}

function classificationPillClass(value: ProductClassification): string {
  switch (value) {
    case "critical":          return "pi-pill-err";
    case "important_class_1":
    case "important_class_2": return "pi-pill-warn";
    default:                  return "pi-pill-flat";
  }
}

function formatLifecycle(value: ProductLifecycleStatus): string {
  return value === "legacy" ? "Legacy" : "Active";
}

function lifecycleHint(value: ProductLifecycleStatus): string {
  return value === "legacy"
    ? "Legacy — on the market pre-CRA, not substantially modified: reporting-only obligations"
    : "Active — subject to the full set of CRA obligations";
}

/**
 * Derives the CRA obligation level from scope + lifecycle — these are not
 * independent axes, so the inventory shows one obligation column instead of two
 * overlapping pills:
 *   out of scope            → no obligations
 *   in scope + legacy       → reporting only (Art. 14 reporting still applies)
 *   in scope + active       → full CRA obligations
 *   scope undecided         → not yet assessed
 */
interface ObligationView {
  label: string;
  pillClass: string;
  hint: string;
}
function obligationView(
  scope: ScopeStatus | string,
  lifecycle: ProductLifecycleStatus,
): ObligationView {
  if (scope === "out_of_scope")
    return {
      label: "None",
      pillClass: "pi-pill-flat",
      hint: "Out of scope — no CRA obligations apply.",
    };
  if (scope !== "in_scope")
    return {
      label: "Not assessed",
      pillClass: "pi-pill-flat",
      hint: "Scope not yet decided — run the scope wizard on the product page.",
    };
  if (lifecycle === "legacy")
    return {
      label: "Reporting only",
      pillClass: "pi-pill-warn",
      hint: "In scope + legacy — only the reporting obligations apply (on the market pre-CRA, not substantially modified).",
    };
  return {
    label: "Full CRA",
    pillClass: "pi-pill-ok",
    hint: "In scope + active — subject to the full set of CRA obligations.",
  };
}

/** Short label for the typed CRA product classification. */
function formatProductType(value: ProductType | string): string {
  switch (value) {
    case "type1_software":              return "SW";
    case "type2_hardware_with_digital": return "SW + HW";
    default:                            return "Untyped";
  }
}

function productTypePillClass(value: ProductType | string): string {
  switch (value) {
    case "type1_software":              return "pi-pill-info";
    case "type2_hardware_with_digital": return "pi-pill-violet";
    default:                            return "pi-pill-flat";
  }
}

/** Label for the product-level conformity assessment route. */
function formatConformityRoute(value: ConformityRoute | string): string {
  switch (value) {
    case "self_assessment":        return "Self-assessment";
    case "third_party_assessment": return "Third-party";
    case "not_applicable":         return "N/A";
    default:                       return "Undecided";
  }
}

function conformityRoutePillClass(value: ConformityRoute | string): string {
  switch (value) {
    case "self_assessment":        return "pi-pill-ok";
    case "third_party_assessment": return "pi-pill-warn";
    case "not_applicable":         return "pi-pill-flat";
    default:                       return "pi-pill-flat";
  }
}

/**
 * Builds the compact "flags" chips for a product row — a scoping fingerprint the
 * auditor can read at a glance. Each flag has a single-letter mark, a colour
 * variant, and a hover title explaining it.
 *   S — sold as a system (SystemProfile)         T — tailor-made B2B terms
 *   R — relies on remote data processing         E — embedded (HW + firmware)
 *   P — pre-CRA (transition provisions)          ⚠ — out-of-scope but unsigned
 */
interface ProductFlag {
  key: string;
  label: string;
  title: string;
  variant: string;
}
/**
 * Accepts either the list summary (which carries the has_* booleans) or the full
 * detail object (which carries the underlying JSON/collections), so the same
 * chips render in both the table and the drawer.
 */
type FlaggableProduct = {
  scope_status: ScopeStatus | string;
  scope_decision_signature: string | null;
  is_embedded_product: boolean;
  is_pre_cra: boolean;
  has_system_profile?: boolean;
  has_tailor_made_terms?: boolean;
  has_remote_processing?: boolean;
  system_profile_json?: unknown;
  tailor_made_terms_json?: unknown;
  remote_processing_elements?: unknown[];
};
function productFlags(product: FlaggableProduct): ProductFlag[] {
  const hasSystem = product.has_system_profile ?? Boolean(product.system_profile_json);
  const hasTailor = product.has_tailor_made_terms ?? Boolean(product.tailor_made_terms_json);
  const hasRemote =
    product.has_remote_processing ?? (product.remote_processing_elements?.length ?? 0) > 0;

  const flags: ProductFlag[] = [];
  if (hasSystem)
    flags.push({ key: "S", label: "S", title: "Sold as a system (system profile set)", variant: "pi-flag-violet" });
  if (hasTailor)
    flags.push({ key: "T", label: "T", title: "Tailor-made — custom B2B contract terms", variant: "pi-flag-cyan" });
  if (hasRemote)
    flags.push({ key: "R", label: "R", title: "Relies on a remote data processing element", variant: "pi-flag-green" });
  if (product.is_embedded_product)
    flags.push({ key: "E", label: "E", title: "Embedded product — hardware with firmware/software", variant: "pi-flag-blue" });
  if (product.is_pre_cra)
    flags.push({ key: "P", label: "P", title: "Pre-CRA — placed on the market before CRA applicability", variant: "pi-flag-amber" });
  if (product.scope_status === "out_of_scope" && !product.scope_decision_signature)
    flags.push({ key: "unsigned", label: "⚠", title: "Out of scope but the decision is not yet signed", variant: "pi-flag-danger" });
  return flags;
}

/** Yes/No/— for nullable booleans in the drawer key-value lists. */
function formatBool(value: boolean | null | undefined): string {
  if (value === null || value === undefined) return "—";
  return value ? "Yes" : "No";
}

// ── Stat-card + scope-tab helpers ──
const outOfScopeCount = computed(() =>
  products.value.filter((p) => p.scope_status === "out_of_scope").length,
);
const remoteProcessingCount = computed(() =>
  products.value.filter((p) => p.has_remote_processing).length,
);
const unsignedOutOfScopeCount = computed(() =>
  products.value.filter((p) => p.scope_status === "out_of_scope" && !p.scope_decision_signature).length,
);

/** Clicking a stat card / scope tab drives the scope filter. */
function setScopeFilter(value: ScopeStatus | ""): void {
  filters.scopeStatus = filters.scopeStatus === value ? "" : value;
}

// ── Drawer open/close + lazy detail fetch ──
function resetDeleteConfirm(): void {
  deleteConfirmOpen.value = false;
  deleteConfirmCode.value = "";
}

async function openDrawer(productId: string): Promise<void> {
  drawerProductId.value = productId;
  drawerProduct.value = null;
  drawerError.value = "";
  drawerLoading.value = true;
  resetDeleteConfirm();
  try {
    drawerProduct.value = await productService.get(productId);
  } catch (error) {
    drawerError.value = error instanceof Error ? error.message : "Failed to load product.";
  } finally {
    drawerLoading.value = false;
  }
}
function closeDrawer(): void {
  drawerProductId.value = null;
  drawerProduct.value = null;
  drawerError.value = "";
  resetDeleteConfirm();
}

/**
 * Deletes the drawer's product after the typed-code confirmation. This cascades
 * to the product's releases, assessments, RPEs and related records, so it is
 * gated behind matching the product code exactly.
 */
async function deleteProduct(): Promise<void> {
  const target = drawerProduct.value;
  if (!target) return;
  if (deleteConfirmCode.value.trim() !== target.product_code) return;

  isDeleting.value = true;
  drawerError.value = "";
  try {
    await productService.remove(target.id);
    closeDrawer();
    await loadProducts();
  } catch (error) {
    drawerError.value = error instanceof Error ? error.message : "Failed to delete product.";
  } finally {
    isDeleting.value = false;
  }
}

function scopePillClass(value: ScopeStatus | string): string {
  switch (value) {
    case "in_scope":     return "pi-pill-ok";
    case "out_of_scope": return "pi-pill-err";
    default:             return "pi-pill-flat";
  }
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat("en-GB", {
    year: "numeric",
    month: "short",
    day: "2-digit",
  }).format(new Date(value));
}

function resetFilters(): void {
  filters.search = "";
  filters.scopeStatus = "";
  filters.classification = "";
  filters.lifecycleStatus = "";
  filters.productType = "";
  filters.conformityRoute = "";
  filters.supportStatus = "";
  filters.updatedWithin = "";
  filters.sortBy = "updated_desc";
}

/**
 * The active category filters (search is excluded — it lives in its own always-
 * visible box). Drives the count badge on the Filters button and the removable
 * chip row: each entry knows its human label, current value, and how to clear
 * itself. Keeping this list in one place means the badge, the chips, and
 * "Clear all" can never drift out of sync.
 */
interface FilterChip {
  key: string;
  label: string;
  value: string;
  clear: () => void;
}
const activeFilterChips = computed<FilterChip[]>(() => {
  const chips: FilterChip[] = [];
  if (filters.scopeStatus)
    chips.push({ key: "scope", label: "Scope", value: formatScopeStatus(filters.scopeStatus), clear: () => (filters.scopeStatus = "") });
  if (filters.classification)
    chips.push({ key: "class", label: "Classification", value: formatClassification(filters.classification), clear: () => (filters.classification = "") });
  if (filters.lifecycleStatus)
    chips.push({ key: "lifecycle", label: "Lifecycle", value: formatLifecycle(filters.lifecycleStatus), clear: () => (filters.lifecycleStatus = "") });
  if (filters.productType)
    chips.push({ key: "type", label: "CRA type", value: formatProductType(filters.productType), clear: () => (filters.productType = "") });
  if (filters.conformityRoute)
    chips.push({ key: "route", label: "Route", value: formatConformityRoute(filters.conformityRoute), clear: () => (filters.conformityRoute = "") });
  if (filters.supportStatus)
    chips.push({ key: "support", label: "Support", value: formatSupportFilter(filters.supportStatus), clear: () => (filters.supportStatus = "") });
  if (filters.updatedWithin)
    chips.push({ key: "updated", label: "Updated", value: `Last ${filters.updatedWithin} days`, clear: () => (filters.updatedWithin = "") });
  return chips;
});
const activeFilterCount = computed(() => activeFilterChips.value.length);

function resetForm(): void {
  form.product_code = "";
  form.name = "";
  form.description = null;
  form.parent_product_id = null;
  form.manufacturer_name = "";
  form.intended_use = "";
  form.product_type = "";
  form.current_classification = "normal";
  form.scope_status = "undecided";
  form.lifecycle_status = "active";
  form.product_type_class = "undecided";
  form.conformity_route = "undecided";
  form.is_embedded_product = false;
  formError.value = "";
}

function toggleCreateForm(): void {
  showCreateForm.value = !showCreateForm.value;
  if (!showCreateForm.value) resetForm();
}

async function loadSupportPeriods(productList: ProductSummaryRead[]): Promise<void> {
  // Fetch the latest-release support period for each product in parallel.
  const entries = await Promise.all(
    productList.map(async (product) => {
      try {
        const record = await supportPeriodService.getActiveForProduct(product.id, {
          latestRelease: true,
        });
        return [product.id, record] as const;
      } catch {
        return [product.id, null] as const;
      }
    }),
  );
  supportByProductId.value = Object.fromEntries(entries);
}

async function loadProducts(): Promise<void> {
  isLoading.value = true;
  errorMessage.value = "";
  try {
    const loadedProducts = await productService.list();
    products.value = loadedProducts;
    await loadSupportPeriods(loadedProducts);
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : "Failed to load products.";
  } finally {
    isLoading.value = false;
  }
}

async function createProduct(): Promise<void> {
  isSubmitting.value = true;
  formError.value = "";
  try {
    const payload: ProductCreate = {
      ...form,
      description: form.description?.trim() || null,
    };
    await productService.create(payload);
    resetForm();
    showCreateForm.value = false;
    await loadProducts();
  } catch (error) {
    formError.value =
      error instanceof Error ? error.message : "Failed to create product.";
  } finally {
    isSubmitting.value = false;
  }
}

function openProduct(productId: string): void {
  router.push({ name: "product-detail", params: { productId } });
}

onMounted(() => {
  void loadProducts();
});
</script>

<style scoped>
/* ─── Page shell ─────────────────────────────────── */
.pi-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ─── Page head ──────────────────────────────────── */
.pi-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  flex-wrap: wrap;
}
.pi-sub {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
}
.pi-head-actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-shrink: 0;
}

/* Buttons rendered by AppButton component */

/* ─── Icons ──────────────────────────────────────── */
.pi-ico    { width: 14px; height: 14px; flex-shrink: 0; }
.pi-ico-sm { width: 13px; height: 13px; flex-shrink: 0; }

/* ─── KPI row ────────────────────────────────────── */
.pi-kpi-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
}
.pi-kpi {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  text-align: left;
  font: inherit;
  color: inherit;
}
/* Clickable KPI cards (Total / In scope / Out of scope) drive the scope filter. */
button.pi-kpi { cursor: pointer; transition: border-color 0.12s, box-shadow 0.12s; }
button.pi-kpi:hover { border-color: var(--color-border-strong); }
.pi-kpi-sel {
  border-color: var(--color-primary) !important;
  box-shadow: 0 0 0 3px rgba(28,107,39,0.10);
}
.pi-kpi-val-ok { color: var(--color-success-text); }
.pi-kpi-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: var(--color-text-muted);
  font-size: 12px;
  font-weight: 500;
}
.pi-kpi-ic {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--color-surface-elevated);
  display: grid;
  place-items: center;
  color: var(--color-text-muted);
}
/* Coloured icon backgrounds by KPI variant */
.pi-kpi-ok .pi-kpi-ic    { background: var(--color-success-bg);  color: var(--color-success); }
.pi-kpi-danger .pi-kpi-ic { background: var(--color-danger-bg);  color: var(--color-danger); }
.pi-kpi-warn .pi-kpi-ic  { background: var(--color-warning-bg); color: var(--color-warning); }

.pi-kpi-val {
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1;
  color: var(--color-text);
}
.pi-kpi-unit { font-size: 13px; color: var(--color-text-muted); font-weight: 500; margin-left: 4px; }
.pi-kpi-foot { display: flex; align-items: center; gap: 6px; font-size: 12px; color: var(--color-text-muted); }

/* ─── Status pills ───────────────────────────────── */
.pi-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.6;
  white-space: nowrap;
}
.pi-pd { width: 6px; height: 6px; border-radius: 50%; }

.pi-pill-ok   { background: var(--color-success-bg); color: var(--color-success-text); }
.pi-pill-ok .pi-pd { background: var(--color-success); }
.pi-pill-warn { background: var(--color-warning-bg); color: var(--color-warning-text); }
.pi-pill-warn .pi-pd { background: var(--color-warning); }
.pi-pill-err  { background: var(--color-danger-bg); color: var(--color-danger-text); }
.pi-pill-err .pi-pd { background: var(--color-danger); }
.pi-pill-flat { background: var(--color-slate-bg); color: var(--color-slate-text); border: 1px dashed var(--color-slate-border); }
.pi-pill-flat .pi-pd { background: var(--color-slate-text); }
/* Extra pill variants for typed classification (info=blue, violet). */
.pi-pill-info   { background: rgba(37,99,168,0.12);  color: #2563a8; }
.pi-pill-violet { background: rgba(124,58,237,0.13); color: #7c3aed; }

/* ─── Flag chips (scoping fingerprint) ───────────── */
.pi-flags { display: inline-flex; align-items: center; gap: 4px; flex-wrap: wrap; }
.pi-flags-empty { color: var(--color-text-muted); }
.pi-flag {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 6px;
  font-size: 11px;
  font-weight: 700;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  flex-shrink: 0;
}
.pi-flag-violet { background: rgba(124,58,237,0.14); color: #7c3aed; }
.pi-flag-cyan   { background: rgba(14,116,144,0.14); color: #0e7490; }
.pi-flag-green  { background: var(--color-success-bg); color: var(--color-success-text); }
.pi-flag-blue   { background: rgba(37,99,168,0.14); color: #2563a8; }
.pi-flag-amber  { background: var(--color-warning-bg); color: var(--color-warning-text); }
.pi-flag-danger { background: var(--color-danger-bg); color: var(--color-danger-text); }
.pi-support-none { font-size: 12px; }

/* ─── Filter toolbar ─────────────────────────────── */
.pi-toolbar {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  padding: 10px 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.pi-filter-search {
  flex: 1;
  min-width: 220px;
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  padding: 7px 11px;
  color: var(--color-text-muted);
}
.pi-filter-search input {
  border: none;
  outline: none;
  background: transparent;
  font: inherit;
  color: var(--color-text);
  flex: 1;
  min-width: 0;
  font-size: 13px;
}
.pi-filter-search input::placeholder { color: var(--color-text-muted); }

/* Filter pill wrapper */
.pi-fpill-wrap {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 32px;
  padding: 0 11px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  position: relative;
  white-space: nowrap;
  transition: background 0.1s, border-color 0.1s;
}
.pi-fpill-wrap:hover { background: var(--color-surface-elevated); }
.pi-fpill-active {
  background: var(--color-success-bg) !important;
  border-color: var(--color-success-border) !important;
  color: var(--color-success-text);
}
.pi-fpill-lbl {
  font-size: 12.5px;
  font-weight: 500;
  pointer-events: none;
  color: var(--color-text-muted);
}
.pi-fpill-active .pi-fpill-lbl { color: var(--color-success-text); }
.pi-fpill-chev {
  width: 12px;
  height: 12px;
  color: var(--color-text-muted);
  pointer-events: none;
  flex-shrink: 0;
}
.pi-fpill-active .pi-fpill-chev { color: var(--color-success-text); }
/* Transparent select overlay — captures clicks for the pill */
.pi-fpill-select {
  position: absolute;
  inset: 0;
  opacity: 0;
  width: 100%;
  cursor: pointer;
  font: inherit;
}

.pi-sort-group { margin-left: auto; }

/* ─── Filters popover ────────────────────────────── */
.pi-pop-wrap { position: relative; display: inline-flex; }
/* Trigger button (matches the filter-pill height/shape) */
.pi-tbtn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 11px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
  font: 500 12.5px/1 inherit;
  color: var(--color-text-muted);
  transition: background 0.1s, border-color 0.1s;
}
.pi-tbtn:hover { background: var(--color-surface-elevated); }
.pi-tbtn-active {
  background: var(--color-success-bg);
  border-color: var(--color-success-border);
  color: var(--color-success-text);
}
.pi-tbtn-count {
  display: inline-grid;
  place-items: center;
  min-width: 17px;
  height: 17px;
  padding: 0 5px;
  border-radius: 999px;
  background: var(--color-success);
  color: #fff;
  font-size: 10.5px;
  font-weight: 700;
}
.pi-tbtn .pi-fpill-chev { width: 12px; height: 12px; }

/* Backdrop that closes the popover on outside click */
.pi-pop-backdrop { position: fixed; inset: 0; z-index: 40; }
.pi-pop-menu {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  z-index: 41;
  width: 260px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 10px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.12);
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.pi-pop-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}
.pi-pop-clear {
  background: none;
  border: none;
  cursor: pointer;
  font: 600 11.5px/1 inherit;
  text-transform: none;
  letter-spacing: 0;
  color: var(--color-primary);
  padding: 0;
}
.pi-pop-clear:hover { text-decoration: underline; }
.pi-pop-field { display: flex; flex-direction: column; gap: 4px; }
.pi-pop-field > span { font-size: 12px; font-weight: 500; color: var(--color-text-muted); }
.pi-pop-foot { display: flex; justify-content: flex-end; padding-top: 2px; }

/* ─── Active-filter chip row ─────────────────────── */
.pi-chip-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.pi-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  height: 26px;
  padding: 0 8px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 999px;
  cursor: pointer;
  font: 500 12px/1 inherit;
  color: var(--color-text);
  transition: background 0.1s, border-color 0.1s;
}
.pi-chip:hover { background: var(--color-danger-bg); border-color: var(--color-danger-border); }
.pi-chip-k { color: var(--color-text-muted); }
.pi-chip-v { font-weight: 600; }
.pi-chip-x { width: 12px; height: 12px; color: var(--color-text-muted); }
.pi-chip:hover .pi-chip-x { color: var(--color-danger-text); }
.pi-chip-clear {
  background: none;
  border: none;
  cursor: pointer;
  font: 600 12px/1 inherit;
  color: var(--color-text-muted);
  padding: 4px 6px;
}
.pi-chip-clear:hover { color: var(--color-text); text-decoration: underline; }

/* ─── Skeleton loader ────────────────────────────── */
.pi-skel-wrap { padding: 6px 0; }
.pi-skel-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  border-bottom: 1px solid var(--color-border);
}
.pi-skel-row:last-child { border-bottom: none; }
.pi-skel {
  background: linear-gradient(90deg, var(--color-surface-elevated) 25%, var(--color-border) 37%, var(--color-surface-elevated) 63%);
  background-size: 400% 100%;
  border-radius: 6px;
  animation: pi-shimmer 1.4s ease-in-out infinite;
}
.pi-skel-mark { width: 36px; height: 36px; border-radius: 9px; flex-shrink: 0; }
.pi-skel-line { height: 12px; }
.pi-skel-pill { width: 68px; height: 20px; border-radius: 999px; flex-shrink: 0; }
.pi-skel-w40 { width: 40%; }
.pi-skel-w20 { width: 20%; margin-left: auto; }
@keyframes pi-shimmer { 0% { background-position: 100% 0; } 100% { background-position: 0 0; } }
@media (prefers-reduced-motion: reduce) { .pi-skel { animation: none; } }

/* ─── Empty state ────────────────────────────────── */
.pi-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 8px;
  padding: 48px 24px;
}
.pi-empty-ic {
  width: 56px;
  height: 56px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  margin-bottom: 4px;
}
.pi-empty-title { margin: 0; font-size: 15px; font-weight: 600; color: var(--color-text); }
.pi-empty-sub { margin: 0 0 8px; font-size: 13px; color: var(--color-text-muted); max-width: 360px; }

/* ─── Shared panel style ──────────────────────────── */
.pi-panel {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: 0 1px 2px rgba(0,0,0,0.04);
  overflow: hidden;
}
.pi-panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 18px;
  border-bottom: 1px solid var(--color-border);
}
.pi-panel-title {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: 10px;
}
.pi-count-pill {
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  font-size: 11.5px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: 999px;
  letter-spacing: 0.02em;
}
.pi-panel-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px 20px;
  flex-wrap: wrap;
  padding: 10px 18px;
  border-top: 1px solid var(--color-border);
  color: var(--color-text-muted);
  font-size: 12.5px;
  background: var(--color-surface-elevated);
}
.pi-panel-foot strong { color: var(--color-text); }
/* Flag legend in the table footer. */
.pi-legend { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.pi-legend-item { display: inline-flex; align-items: center; gap: 6px; font-size: 11.5px; color: var(--color-text-muted); }
.pi-legend-item .pi-flag { width: 18px; height: 18px; font-size: 10px; }

/* ─── State messages ─────────────────────────────── */
.pi-state {
  padding: 28px 20px;
  text-align: center;
  color: var(--color-text-muted);
  font-size: 13.5px;
}
.pi-state-err { color: var(--color-danger-text); }

/* ─── Table ──────────────────────────────────────── */
.pi-table-wrap { overflow-x: auto; }
.pi-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.pi-table thead th {
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 12px 14px;
  background: var(--color-surface-elevated);
  border-bottom: 1px solid var(--color-border);
  white-space: nowrap;
  position: sticky;
  top: 0;
  z-index: 1;
}
.pi-table tbody td {
  padding: 14px;
  border-bottom: 1px solid var(--color-border);
  color: var(--color-text-muted);
  vertical-align: middle;
}
.pi-table tbody tr:last-child td { border-bottom: none; }
.pi-row { cursor: pointer; transition: background 0.12s; }
.pi-row:hover td { background: var(--color-surface-elevated); }
.pi-row-flagged td { background: var(--color-danger-bg); }
.pi-row-flagged:hover td { background: rgba(255,125,125,0.14); }

/* Product cell */
.pi-prod-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}
.pi-prod-mark {
  width: 36px;
  height: 36px;
  border-radius: 9px;
  background: var(--color-surface-elevated);
  border: 1px solid var(--color-border);
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-muted);
  flex-shrink: 0;
  letter-spacing: 0.03em;
}
.pi-prod-mark-danger {
  background: var(--color-danger-bg);
  color: var(--color-danger-text);
  border-color: var(--color-danger-border);
}
.pi-prod-name { font-weight: 600; color: var(--color-text); white-space: nowrap; }
.pi-prod-sub  { font-size: 11.5px; color: var(--color-text-muted); margin-top: 2px; white-space: nowrap; max-width: 180px; overflow: hidden; text-overflow: ellipsis; }

/* Misc cells */
.pi-mono { font-family: 'JetBrains Mono', 'Fira Code', monospace; font-size: 12px; color: var(--color-text); }
.pi-muted { color: var(--color-text-muted); }
.pi-cell-clip { max-width: 130px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }
.pi-support-meta { font-size: 11px; color: var(--color-text-muted); margin-top: 4px; white-space: nowrap; }

/* "Set period" dashed button */
.pi-set-link {
  font-size: 12px;
  color: var(--color-text-muted);
  border: 1px dashed var(--color-border-strong);
  background: transparent;
  padding: 3px 9px;
  border-radius: 999px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: 500 12px/1 inherit;
  transition: background 0.12s, color 0.12s, border-color 0.12s;
}
.pi-set-link:hover {
  color: var(--color-success-text);
  border-color: var(--color-success);
  border-style: solid;
  background: var(--color-success-bg);
}

/* Row chevron (drawer affordance) */
.pi-action-cell { text-align: right; white-space: nowrap; width: 36px; }
.pi-row-chev {
  width: 15px;
  height: 15px;
  color: var(--color-text-muted);
  opacity: 0;
  transition: opacity 0.1s, transform 0.1s;
}
.pi-row:hover .pi-row-chev { opacity: 1; }
.pi-row-active td { background: var(--color-surface-elevated) !important; }
.pi-row-active .pi-row-chev { opacity: 1; color: var(--color-primary); }

/* ─── Create form panel ──────────────────────────── */
.pi-form-panel { padding: 18px; }
.pi-form-head { margin-bottom: 16px; }
.pi-form-title { margin: 0 0 4px; font-size: 15px; font-weight: 600; color: var(--color-text); }
.pi-form-sub { margin: 0; }
.pi-form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
}
.pi-field { display: grid; gap: 5px; }
.pi-field-span2 { grid-column: span 2; }
.pi-field-lbl { font-size: 12.5px; font-weight: 500; color: var(--color-text-muted); }
.pi-field-hint { font-size: 11.5px; font-weight: 400; margin-left: 4px; }
.pi-field-checkbox { display: flex; flex-direction: row; align-items: flex-start; gap: 8px; padding: 6px 0; cursor: pointer; }
.pi-field-checkbox input[type="checkbox"] { margin-top: 2px; flex-shrink: 0; }
.pi-input, .pi-select, .pi-textarea {
  width: 100%;
  box-sizing: border-box;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
  color: var(--color-text);
  padding: 8px 11px;
  font: inherit;
  font-size: 13px;
  outline: none;
  transition: border-color 0.12s;
}
.pi-input:focus, .pi-select:focus, .pi-textarea:focus { border-color: var(--color-primary); }
.pi-textarea { resize: vertical; }
.pi-parent-picker { display: flex; gap: 8px; align-items: center; }
.pi-parent-trigger { flex: 1; text-align: left; cursor: pointer; }
.pi-parent-clear {
  flex-shrink: 0;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text-muted);
  padding: 4px 8px;
  cursor: pointer;
  font-size: 12px;
  line-height: 1;
}
.pi-parent-clear:hover { color: var(--color-danger); }
.pi-form-actions { display: flex; align-items: center; gap: 12px; justify-content: flex-end; }
.pi-form-error { font-size: 12.5px; color: var(--color-danger-text); margin: 0; }

/* ─── Parent picker modal ────────────────────────── */
.pi-picker-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.pi-picker-title { margin: 0; font-size: 15px; font-weight: 600; }
.pi-picker-close {
  background: none;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  color: var(--color-text-muted);
  padding: 4px;
  cursor: pointer;
  display: grid;
  place-items: center;
}
.pi-picker-close:hover { color: var(--color-text); background: var(--color-surface-elevated); }
.pi-picker-list { overflow-y: auto; display: flex; flex-direction: column; gap: 3px; margin-top: 10px; max-height: 300px; }
.pi-picker-empty { padding: 12px; font-size: 13px; margin: 0; }
.pi-picker-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  text-align: left;
  background: none;
  border: 1px solid transparent;
  border-radius: 8px;
  padding: 8px 10px;
  cursor: pointer;
  color: inherit;
  font: inherit;
  transition: background 0.1s;
}
.pi-picker-item:hover { background: var(--color-surface-elevated); }
.pi-picker-item-sel { border-color: var(--color-primary); background: var(--color-success-bg); }
.pi-picker-item-row { display: flex; align-items: baseline; gap: 8px; min-width: 0; }
.pi-picker-code {
  flex-shrink: 0;
  font-size: 11px;
  font-weight: 600;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  border-radius: 4px;
  padding: 1px 5px;
}
.pi-picker-name { font-size: 13px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; color: var(--color-text); }
.pi-picker-mfr { font-size: 11.5px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

@media (max-width: 1200px) {
  .pi-kpi-row { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 800px) {
  .pi-kpi-row { grid-template-columns: 1fr; }
  .pi-form-grid { grid-template-columns: 1fr; }
  .pi-field-span2 { grid-column: span 1; }
}
</style>

<style>
/* ── Picker modal (Teleport → body, must be unscoped) ── */
.pi-picker-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.pi-picker-modal {
  width: 100%;
  max-width: 520px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  padding: 20px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: 14px;
  box-shadow: 0 8px 40px rgba(0,0,0,0.35);
  overflow: hidden;
}

/* ── Right-side detail drawer (Teleport → body, unscoped) ── */
.pi-drawer-scrim {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(16, 24, 40, 0.36);
  animation: piScrimIn 0.15s ease;
}
@keyframes piScrimIn { from { opacity: 0; } to { opacity: 1; } }
.pi-drawer {
  position: fixed;
  top: 0;
  right: 0;
  height: 100vh;
  width: 540px;
  max-width: 92vw;
  z-index: 1001;
  background: var(--color-surface);
  border-left: 1px solid var(--color-border);
  box-shadow: -12px 0 40px rgba(16, 24, 40, 0.20);
  display: flex;
  flex-direction: column;
  animation: piDrawerIn 0.22s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes piDrawerIn { from { transform: translateX(28px); opacity: 0.4; } to { transform: translateX(0); opacity: 1; } }
.pi-drawer-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
  padding: 20px 22px;
  border-bottom: 1px solid var(--color-border);
}
.pi-drawer-head-main { display: flex; flex-direction: column; gap: 7px; min-width: 0; }
.pi-drawer-code { font-size: 12px; color: var(--color-primary); font-weight: 500; }
.pi-drawer-title { margin: 0; font-size: 19px; font-weight: 600; letter-spacing: -0.01em; line-height: 1.25; color: var(--color-text); }
.pi-drawer-badges { display: flex; gap: 7px; flex-wrap: wrap; margin-top: 2px; }
.pi-drawer-close {
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: none;
  background: var(--color-surface-elevated);
  color: var(--color-text-muted);
  cursor: pointer;
  display: grid;
  place-items: center;
}
.pi-drawer-close:hover { background: var(--color-surface-elevated-strong); color: var(--color-text); }
.pi-drawer-body { flex: 1; overflow-y: auto; padding: 20px 22px; display: flex; flex-direction: column; gap: 22px; }
.pi-drawer-foot {
  display: flex;
  gap: 10px;
  align-items: center;
  justify-content: flex-end;
  padding: 14px 22px;
  border-top: 1px solid var(--color-border);
  background: var(--color-surface-elevated);
}
/* Ghost danger "Delete" trigger — sits between the primary and Close buttons. */
.pi-del-trigger {
  margin-right: auto;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: 1px solid var(--color-danger-border);
  color: var(--color-danger-text);
  border-radius: 8px;
  padding: 7px 12px;
  font: 500 13px/1 inherit;
  cursor: pointer;
  transition: background 0.12s;
}
.pi-del-trigger:hover { background: var(--color-danger-bg); }
/* Typed-code confirmation panel replaces the footer buttons while active. */
.pi-del-confirm { width: 100%; display: flex; flex-direction: column; gap: 8px; }
/* .pi-mono is scoped; redeclare for the teleported drawer's code references. */
.pi-drawer .pi-mono, .pi-del-confirm .pi-mono {
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 12px;
  color: var(--color-text);
}
.pi-del-warn { margin: 0; font-size: 12.5px; line-height: 1.5; color: var(--color-danger-text); }
.pi-del-label { font-size: 12px; color: var(--color-text-muted); }
/* Self-contained input styling — scoped .pi-input does not reach the teleported drawer. */
.pi-del-input {
  max-width: 280px;
  box-sizing: border-box;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  padding: 8px 11px;
  font: inherit;
  font-size: 13px;
  outline: none;
}
.pi-del-input:focus { border-color: var(--color-danger-border); }
.pi-del-actions { display: flex; gap: 8px; margin-top: 2px; }

.pi-drawer-flagrow { display: flex; flex-direction: column; gap: 8px; }
/* Each flag on its own line: fixed-size letter chip + explanatory label. */
.pi-flag-line { display: flex; align-items: center; gap: 10px; }
.pi-flag-line .pi-flag { flex-shrink: 0; }
.pi-flag-txt { font-size: 12.5px; color: var(--color-text); line-height: 1.35; }

.pi-drawer-sec { display: flex; flex-direction: column; gap: 10px; }
.pi-drawer-sec-title {
  margin: 0;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--color-text-muted);
}
.pi-sec-note { text-transform: none; letter-spacing: 0; font-weight: 400; color: var(--color-text-muted); opacity: 0.7; }

.pi-kv { margin: 0; display: flex; flex-direction: column; }
.pi-kv-row {
  display: grid;
  grid-template-columns: 148px 1fr;
  gap: 12px;
  padding: 8px 0;
  border-bottom: 1px solid var(--color-border);
  font-size: 13px;
  align-items: baseline;
}
.pi-kv-row:last-child { border-bottom: none; }
.pi-kv-row dt { margin: 0; color: var(--color-text-muted); font-size: 12px; }
.pi-kv-row dd { margin: 0; color: var(--color-text); }
.pi-kv-long { line-height: 1.5; }

.pi-scope-box { border-radius: 10px; padding: 4px 14px; }
.pi-scope-box-in { background: var(--color-success-bg); }
.pi-scope-box-out { background: var(--color-warning-bg); }
.pi-scope-empty { padding: 10px 0; margin: 0; font-size: 13px; }

.pi-rdps-list { display: flex; flex-direction: column; gap: 8px; }
.pi-rdps-item { border: 1px solid var(--color-border); border-radius: 9px; padding: 10px 13px; }
.pi-rdps-name { font-size: 13px; font-weight: 600; color: var(--color-text); }
.pi-rdps-meta { font-size: 11.5px; color: var(--color-text-muted); margin-top: 2px; }

:root[data-theme="light"] .pi-drawer { background: #fff; }

/* Light mode overrides */
:root[data-theme="light"] .pi-row-flagged td { background: rgba(200,95,95,0.07); }
:root[data-theme="light"] .pi-row-flagged:hover td { background: rgba(200,95,95,0.11); }
:root[data-theme="light"] .pi-row:hover td { background: rgba(28,107,39,0.04); }
:root[data-theme="light"] .pi-picker-modal { background: #fff; }
:root[data-theme="light"] .pi-picker-item:hover { background: rgba(0,0,0,0.04); }
:root[data-theme="light"] .pi-picker-item-sel { background: rgba(28,107,39,0.06); border-color: rgba(28,107,39,0.5); }
</style>
