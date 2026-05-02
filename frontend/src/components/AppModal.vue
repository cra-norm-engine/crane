<template>
  <!--
    AppModal — reusable dialog overlay.

    Bind with v-model to control visibility.
    Default slot = body content. Named slot "footer" = action buttons.

    Features:
    - Teleported to the document body to avoid z-index stacking issues.
    - Closes on Escape key or backdrop click (unless persistent=true).
    - Smooth scale + fade enter/leave transition.
    - Scroll-lock on the document body while open.
    - Three size variants: sm / md / lg.
    - Accessible: role="dialog", aria-modal, aria-labelledby.
  -->
  <Teleport to="body">
    <Transition name="modal">
      <div
        v-if="modelValue"
        class="modal-backdrop"
        role="dialog"
        aria-modal="true"
        :aria-labelledby="titleId"
        @click.self="handleBackdropClick"
        @keydown.esc="close"
      >
        <!-- ── Modal panel ────────────────────────────── -->
        <div
          ref="panelRef"
          class="modal-panel"
          :class="`modal-panel-${size}`"
          tabindex="-1"
        >

          <!-- ── Header ─────────────────────────────── -->
          <div class="modal-header">
            <h2 :id="titleId" class="modal-title">{{ title }}</h2>

            <!-- Close (×) button in the top-right corner -->
            <button
              class="modal-close icon-btn"
              type="button"
              aria-label="Close dialog"
              @click="close"
            >
              <!-- × icon -->
              <svg
                viewBox="0 0 20 20"
                width="16"
                height="16"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
                aria-hidden="true"
              >
                <line x1="5" y1="5" x2="15" y2="15" />
                <line x1="15" y1="5" x2="5"  y2="15" />
              </svg>
            </button>
          </div>

          <!-- ── Body — default slot ────────────────── -->
          <div class="modal-body">
            <slot />
          </div>

          <!-- ── Footer — optional slot ─────────────── -->
          <div v-if="$slots.footer" class="modal-footer">
            <slot name="footer" />
          </div>

        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from "vue";

/* ── Unique ID for aria-labelledby ───────────────── */
/* Each modal instance gets its own ID so multiple modals
   on the same page don't share aria attributes. */
let idCounter = 0;
const titleId = `modal-title-${++idCounter}`;

/* ── Props ───────────────────────────────────────── */
const props = withDefaults(
  defineProps<{
    /** Controls visibility — bind with v-model */
    modelValue: boolean;
    /** Heading text shown in the modal header */
    title: string;
    /**
     * Panel width variant:
     * sm  — 400 px  (confirmations, simple prompts)
     * md  — 600 px  (forms, detail views)  ← default
     * lg  — 820 px  (complex forms, tables)
     */
    size?: "sm" | "md" | "lg";
    /**
     * When true, clicking the backdrop does NOT close the modal.
     * Useful for forms with unsaved changes.
     */
    persistent?: boolean;
  }>(),
  {
    size: "md",
    persistent: false,
  },
);

/* ── Emits ───────────────────────────────────────── */
const emit = defineEmits<{
  /** Fired whenever the modal should close — parent must update v-model */
  "update:modelValue": [value: boolean];
}>();

/* ── Template refs ───────────────────────────────── */
const panelRef = ref<HTMLElement | null>(null);

/* ── Close helpers ───────────────────────────────── */

/** Emit the close event so the parent's v-model becomes false */
function close(): void {
  emit("update:modelValue", false);
}

/** Only close on backdrop click when not in persistent mode */
function handleBackdropClick(): void {
  if (!props.persistent) close();
}

/* ── Scroll lock ─────────────────────────────────── */
/* Prevent the page behind the modal from scrolling while the
   dialog is open — restores overflow when the modal closes. */
watch(
  () => props.modelValue,
  (open) => {
    document.body.style.overflow = open ? "hidden" : "";

    if (open) {
      // Focus the panel on next tick so keyboard navigation works
      setTimeout(() => panelRef.value?.focus(), 50);
    }
  },
);

/* ── Keyboard handler ────────────────────────────── */
function handleGlobalKeyDown(e: KeyboardEvent): void {
  if (e.key === "Escape" && props.modelValue) {
    close();
  }
}

/* Register/deregister the global Escape listener */
onMounted(() => {
  document.addEventListener("keydown", handleGlobalKeyDown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleGlobalKeyDown);
  // Always restore scroll when the component is destroyed
  document.body.style.overflow = "";
});
</script>

<style scoped>
/* ── Backdrop ─────────────────────────────────────── */
.modal-backdrop {
  /* Cover the entire viewport */
  position: fixed;
  inset: 0;
  z-index: 200;

  /* Semi-transparent dark overlay */
  background: var(--color-modal-backdrop);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);

  /* Centre the panel in the viewport */
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
  box-sizing: border-box;
}

/* ── Modal panel ──────────────────────────────────── */
.modal-panel {
  /* The panel itself has a scroll container so long forms don't overflow */
  position: relative;
  width: 100%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;

  /* Visual styling consistent with .card in styles.css */
  background: var(--color-modal-bg);
  border: 1px solid var(--color-modal-border);
  border-radius: var(--radius-xl, 20px);
  box-shadow:
    0 32px 80px rgba(0, 0, 0, 0.48),
    0 0 0 1px rgba(255, 255, 255, 0.04);

  /* Remove the browser's default focus ring; we manage focus ourselves */
  outline: none;
}

/* ── Size variants ────────────────────────────────── */
.modal-panel-sm { max-width: 420px; }
.modal-panel-md { max-width: 620px; }
.modal-panel-lg { max-width: 860px; }

/* ── Header ───────────────────────────────────────── */
.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1.35rem 1.5rem 1rem;
  border-bottom: 1px solid var(--color-modal-header-border);
  flex-shrink: 0; /* never squish the header */
}

.modal-title {
  margin: 0;
  font-size: var(--text-xl);
  font-weight: 700;
  line-height: 1.3;
  color: var(--color-text);
}

/* Close button — uses the global .icon-btn utility */
.modal-close {
  margin-top: 0.1rem; /* subtle vertical alignment with the title */
  flex-shrink: 0;
}

/* ── Body ─────────────────────────────────────────── */
.modal-body {
  /* Allow the body to scroll when content is taller than 90 vh */
  overflow-y: auto;
  padding: 1.25rem 1.5rem;
  flex: 1;

  /* Thin themed scrollbar inside the modal body */
  scrollbar-width: thin;
  scrollbar-color: var(--color-primary) transparent;
}

/* ── Footer ───────────────────────────────────────── */
.modal-footer {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid var(--color-modal-header-border);
  flex-shrink: 0;
  flex-wrap: wrap; /* allow buttons to wrap on small screens */
}

/* ── Vue Transition ───────────────────────────────── */
/* Backdrop fades in/out */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.22s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

/* Panel scales up slightly on enter, shrinks on leave */
.modal-enter-active .modal-panel {
  transition: transform 0.25s cubic-bezier(0.34, 1.56, 0.64, 1), opacity 0.22s ease;
}

.modal-leave-active .modal-panel {
  transition: transform 0.18s ease, opacity 0.18s ease;
}

.modal-enter-from .modal-panel {
  transform: scale(0.94) translateY(10px);
  opacity: 0;
}

.modal-leave-to .modal-panel {
  transform: scale(0.96);
  opacity: 0;
}

/* ── Responsive ───────────────────────────────────── */
@media (max-width: 640px) {
  .modal-backdrop {
    /* On very small screens let the panel fill more of the viewport */
    padding: 0.75rem;
    align-items: flex-end; /* sheet-style — panel slides up from bottom */
  }

  .modal-panel {
    max-height: 95vh;
    border-bottom-left-radius: 0;
    border-bottom-right-radius: 0;
  }
}
</style>
