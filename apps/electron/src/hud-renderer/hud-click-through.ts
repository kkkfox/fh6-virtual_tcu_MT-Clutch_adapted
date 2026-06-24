import type { Ref } from 'vue'
import { onUnmounted, watch } from 'vue'

function hitInteractive(x: number, y: number): boolean {
  const el = document.elementFromPoint(x, y)
  return !!el?.closest('.interactive')
}

function insideHudFrame(x: number, y: number): boolean {
  const frame = document.querySelector('.hud-frame')
  if (!frame) return false
  const r = frame.getBoundingClientRect()
  return x >= r.left && x <= r.right && y >= r.top && y <= r.bottom
}

/** Sync Electron setIgnoreMouseEvents with .interactive hit targets while click-through is on. */
export function useHudClickThrough(
  clickThrough: Ref<boolean>,
  applyMouseIgnore: (ignore: boolean) => void,
) {
  function syncFromPointer(e: { clientX: number; clientY: number }) {
    if (!clickThrough.value) {
      applyMouseIgnore(false)
      return
    }
    if (!insideHudFrame(e.clientX, e.clientY)) {
      applyMouseIgnore(true)
      return
    }
    applyMouseIgnore(!hitInteractive(e.clientX, e.clientY))
  }

  function onDocumentPointerMove(e: PointerEvent) {
    syncFromPointer(e)
  }

  function bindDocumentListeners() {
    document.addEventListener('pointermove', onDocumentPointerMove, { passive: true })
    document.addEventListener('pointerdown', onDocumentPointerMove, { passive: true })
  }

  function unbindDocumentListeners() {
    document.removeEventListener('pointermove', onDocumentPointerMove)
    document.removeEventListener('pointerdown', onDocumentPointerMove)
  }

  watch(
    clickThrough,
    (on) => {
      if (on) {
        bindDocumentListeners()
      } else {
        unbindDocumentListeners()
        applyMouseIgnore(false)
      }
    },
    { immediate: true },
  )

  onUnmounted(unbindDocumentListeners)

  return { syncFromPointer }
}
