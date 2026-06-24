import type { HudTemplateId } from '@virtual-tcu/shared/config/hud'
import type { Ref } from 'vue'
import { getHudTemplateLayout, normalizeHudTemplate } from '@virtual-tcu/shared/config/hud'
import { nextTick, onMounted, onUnmounted, watch } from 'vue'

function clampSize(
  width: number,
  height: number,
  template: HudTemplateId,
): { width: number; height: number } {
  const layout = getHudTemplateLayout(template)
  return {
    width: Math.max(layout.minWidth, Math.min(layout.maxWidth, Math.ceil(width))),
    height: Math.max(layout.minHeight, Math.ceil(height)),
  }
}

function measureHudFrame(template: HudTemplateId): { width: number; height: number } | null {
  const frame = document.querySelector('.hud-frame') as HTMLElement | null
  if (!frame) return null

  const width = frame.offsetWidth
  const height = frame.offsetHeight
  if (width <= 0 || height <= 0) return null

  return clampSize(width, height, template)
}

async function syncHudWindowSize(template: HudTemplateId): Promise<void> {
  await nextTick()
  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      const size = measureHudFrame(template)
      if (!size || !window.hud?.setSize) return
      void window.hud.setSize(size.width, size.height)
    })
  })
}

/** Keeps the frameless Electron window sized to HUD content. */
export function useHudWindowSync(deps: {
  hudTemplate: Ref<string>
  connected: Ref<boolean>
  live: Ref<boolean>
  showShiftAdvisor: Ref<boolean>
  showShiftBanner: Ref<boolean>
  clickThrough: Ref<boolean>
}) {
  let observer: ResizeObserver | null = null

  const templateId = (): HudTemplateId => normalizeHudTemplate(deps.hudTemplate.value)

  onMounted(() => {
    observeFrame()
    void syncHudWindowSize(templateId())
  })

  function observeFrame() {
    observer?.disconnect()
    const el = document.querySelector('.hud-frame')
    if (!el) return
    observer = new ResizeObserver(() => {
      void syncHudWindowSize(templateId())
    })
    observer.observe(el)
    for (const child of el.children) observer.observe(child)
  }

  onUnmounted(() => {
    observer?.disconnect()
    observer = null
  })

  watch(
    () => deps.hudTemplate.value,
    () => {
      void nextTick().then(() => {
        observeFrame()
        void syncHudWindowSize(templateId())
      })
    },
  )

  watch(
    () => [
      deps.connected.value,
      deps.live.value,
      deps.showShiftAdvisor.value,
      deps.showShiftBanner.value,
      deps.clickThrough.value,
    ],
    () => {
      void nextTick().then(() => {
        observeFrame()
        void syncHudWindowSize(templateId())
      })
    },
  )
}
