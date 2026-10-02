<template>
  <div class="scope-picker">
    <div class="scope-heading">
      <div>
        <span class="field-label">Policy coverage <span class="req">*</span></span>
        <p class="scope-intro">Choose who this disclosure policy applies to.</p>
      </div>
      <span class="scope-summary">{{ summary }}</span>
    </div>

    <div class="scope-options" role="radiogroup" aria-label="Policy coverage">
      <label class="scope-option" :class="{ active: organizationWide }">
        <input
          type="radio"
          :name="scopeName"
          :checked="organizationWide"
          @change="$emit('update:organizationWide', true)"
        />
        <span class="scope-option-copy">
          <strong>Organization-wide</strong>
          <small>One policy covers every current and future product.</small>
        </span>
        <span class="scope-check" aria-hidden="true">{{ organizationWide ? "✓" : "" }}</span>
      </label>

      <label class="scope-option" :class="{ active: !organizationWide }">
        <input
          type="radio"
          :name="scopeName"
          :checked="!organizationWide"
          @change="$emit('update:organizationWide', false)"
        />
        <span class="scope-option-copy">
          <strong>Selected products</strong>
          <small>Share this policy across a specific product group.</small>
        </span>
        <span class="scope-check" aria-hidden="true">{{ !organizationWide ? "✓" : "" }}</span>
      </label>
    </div>

    <div v-if="!organizationWide" class="product-picker">
      <div class="product-toolbar">
        <label class="product-search">
          <span class="sr-only">Search products</span>
          <span aria-hidden="true">⌕</span>
          <input v-model.trim="query" type="search" placeholder="Search by product name or code…" />
        </label>
        <span class="selected-count">{{ productIds.length }} selected</span>
      </div>

      <div class="product-list" role="group" aria-label="Products covered by this policy">
        <label
          v-for="product in filteredProducts"
          :key="product.id"
          class="product-option"
          :class="{ selected: productIds.includes(product.id) }"
        >
          <input
            type="checkbox"
            :checked="productIds.includes(product.id)"
            @change="toggleProduct(product.id)"
          />
          <span>
            <strong>{{ product.name }}</strong>
            <small>{{ product.product_code }}</small>
          </span>
        </label>
        <div v-if="filteredProducts.length === 0" class="product-empty">
          No products match “{{ query }}”.
        </div>
      </div>

      <p v-if="productIds.length === 0" class="scope-error" role="alert">
        Select at least one product.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, useId } from "vue";

interface ProductOption {
  id: string;
  name: string;
  product_code: string;
}

const props = defineProps<{
  organizationWide: boolean;
  productIds: string[];
  products: ProductOption[];
}>();

const emit = defineEmits<{
  "update:organizationWide": [value: boolean];
  "update:productIds": [value: string[]];
}>();


const scopeName = useId();
const query = ref("");

const filteredProducts = computed(() => {
  const needle = query.value.toLowerCase();
  return [...props.products]
    .sort((a, b) => a.name.localeCompare(b.name))
    .filter((product) =>
      !needle || `${product.name} ${product.product_code}`.toLowerCase().includes(needle),
    );
});

const summary = computed(() => {
  if (props.organizationWide) return "All products";
  return props.productIds.length === 1 ? "1 product" : `${props.productIds.length} products`;
});

function toggleProduct(productId: string): void {
  emit(
    "update:productIds",
    props.productIds.includes(productId)
      ? props.productIds.filter((id) => id !== productId)
      : [...props.productIds, productId],
  );
}
</script>

<style scoped>
.scope-picker {
  display: grid;
  gap: 1rem;
  padding: 1.1rem;
  border: 1px solid var(--color-border, #d9e1ec);
  border-radius: 12px;
  background: var(--color-surface-soft);
}

.scope-heading,
.product-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.scope-intro {
  margin: 0.2rem 0 0;
  color: var(--color-text-muted, #64748b);
  font-size: 0.85rem;
}

.scope-summary,
.selected-count {
  flex: none;
  padding: 0.25rem 0.55rem;
  border-radius: 999px;
  background: var(--color-status-bg);
  color: var(--color-status-text);
  font-size: 0.75rem;
  font-weight: 700;
}

.scope-options {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.75rem;
}

.scope-option {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: start;
  gap: 0.7rem;
  min-height: 78px;
  padding: 0.9rem;
  border: 1px solid var(--color-border, #d9e1ec);
  border-radius: 10px;
  background: var(--color-surface, #fff);
  cursor: pointer;
  transition: border-color 120ms ease, box-shadow 120ms ease, background 120ms ease;
}

.scope-option:hover {
  border-color: var(--color-primary-2);
}

.scope-option.active {
  border-color: var(--color-primary);
  background: var(--color-status-bg);
  box-shadow: 0 0 0 2px var(--color-status-bg);
}

.scope-option input {
  margin-top: 0.15rem;
  accent-color: var(--color-primary);
}

.scope-option-copy {
  display: grid;
  gap: 0.25rem;
}

.scope-option-copy strong,
.product-option strong {
  color: var(--color-text, #172033);
  font-size: 0.9rem;
}

.scope-option-copy small,
.product-option small {
  color: var(--color-text-muted, #64748b);
  font-size: 0.78rem;
  line-height: 1.35;
}

.scope-check {
  display: grid;
  width: 1.25rem;
  height: 1.25rem;
  place-items: center;
  border-radius: 50%;
  background: var(--color-primary);
  color: white;
  font-size: 0.75rem;
  font-weight: 800;
}

.scope-option:not(.active) .scope-check {
  background: transparent;
}

.product-picker {
  display: grid;
  gap: 0.75rem;
  padding-top: 0.25rem;
}

.product-search {
  display: flex;
  flex: 1;
  align-items: center;
  gap: 0.5rem;
  max-width: 28rem;
  padding: 0 0.75rem;
  border: 1px solid var(--color-border, #d9e1ec);
  border-radius: 8px;
  background: var(--color-surface, #fff);
  color: var(--color-text-muted, #64748b);
}

.product-search:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-status-bg);
}

.product-search input {
  width: 100%;
  border: 0;
  padding: 0.65rem 0;
  outline: 0;
  background: transparent;
}

.product-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.5rem;
  max-height: 230px;
  overflow-y: auto;
  padding: 0.15rem;
}

.product-option {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  padding: 0.7rem 0.75rem;
  border: 1px solid var(--color-border, #d9e1ec);
  border-radius: 8px;
  background: var(--color-surface, #fff);
  cursor: pointer;
}

.product-option:hover {
  border-color: var(--color-primary-2);
}

.product-option.selected {
  border-color: var(--color-primary);
  background: var(--color-status-bg);
}

.product-option input {
  flex: none;
  accent-color: var(--color-primary);
}

.product-option span {
  display: grid;
  min-width: 0;
}

.product-empty {
  grid-column: 1 / -1;
  padding: 1rem;
  color: var(--color-text-muted, #64748b);
  text-align: center;
}

.scope-error {
  margin: 0;
  color: #b42318;
  font-size: 0.78rem;
  font-weight: 600;
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

@media (max-width: 680px) {
  .scope-options,
  .product-list {
    grid-template-columns: 1fr;
  }

  .scope-heading,
  .product-toolbar {
    align-items: stretch;
    flex-direction: column;
  }
}
</style>
