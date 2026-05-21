import { reactive, readonly } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
  id: string
  type: ToastType
  message: string
  duration?: number
}

const toasts = reactive<Toast[]>([])

function generateId(): string {
  return Math.random().toString(36).substring(2, 11)
}

export function useToast() {
  function showToast(opts: { type: ToastType; message: string; duration?: number }) {
    const id = generateId()
    const duration = opts.duration ?? 5000
    toasts.push({ id, ...opts, duration })

    if (duration > 0) {
      setTimeout(() => dismissToast(id), duration)
    }
  }

  function dismissToast(id: string) {
    const index = toasts.findIndex((t) => t.id === id)
    if (index !== -1) {
      toasts.splice(index, 1)
    }
  }

  return { toasts: readonly(toasts), showToast, dismissToast }
}
