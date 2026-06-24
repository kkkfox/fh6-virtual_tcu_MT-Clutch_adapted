import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'
import type { Ref } from 'vue'
import { computed } from 'vue'

export function useHudShiftBanner(advice: Ref<ShiftAdvice>, show: Ref<boolean>) {
  const isUp = computed(() => show.value && advice.value === 'up')
  const isDown = computed(() => show.value && advice.value === 'down')
  const label = computed(() => (isDown.value ? 'DOWNSHIFT' : 'UPSHIFT'))
  const chevLeft = computed(() => (isDown.value ? '<<' : '>>'))
  const chevRight = computed(() => (isDown.value ? '<<' : '>>'))

  return { isUp, isDown, label, chevLeft, chevRight }
}
