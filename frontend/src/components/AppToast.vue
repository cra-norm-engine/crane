<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { toasts, dismissToast } = useToast()
</script>

<template>
  <div class="toast-container">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      :class="['toast', `toast-${toast.type}`]"
      role="alert"
      aria-live="polite"
    >
      <div class="toast-content">
        <span v-if="toast.type === 'success'" class="toast-icon">✓</span>
        <span v-else-if="toast.type === 'error'" class="toast-icon">✕</span>
        <span v-else-if="toast.type === 'warning'" class="toast-icon">!</span>
        <span v-else-if="toast.type === 'info'" class="toast-icon">i</span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
      <button
        class="toast-dismiss"
        @click="dismissToast(toast.id)"
        aria-label="Dismiss notification"
      >
        ×
      </button>
    </div>
  </div>
</template>

<style scoped>
.toast-container {
  position: fixed;
  bottom: 1.5rem;
  right: 1.5rem;
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 400px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-radius: 4px;
  font-size: 0.875rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease-out;
  pointer-events: auto;
}

.toast-success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.toast-error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.toast-warning {
  background-color: #fff3cd;
  color: #856404;
  border: 1px solid #ffeeba;
}

.toast-info {
  background-color: #d1ecf1;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.toast-content {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.toast-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  min-width: 20px;
}

.toast-message {
  line-height: 1.4;
}

.toast-dismiss {
  background: none;
  border: none;
  color: inherit;
  font-size: 1.25rem;
  cursor: pointer;
  padding: 0;
  margin-left: 0.5rem;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.toast-dismiss:hover {
  opacity: 1;
}

@keyframes slideIn {
  from {
    transform: translateX(400px);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

@media (max-width: 640px) {
  .toast-container {
    bottom: 1rem;
    right: 1rem;
    left: 1rem;
    max-width: none;
  }

  .toast {
    padding: 0.625rem 0.875rem;
    font-size: 0.8125rem;
  }
}
</style>
