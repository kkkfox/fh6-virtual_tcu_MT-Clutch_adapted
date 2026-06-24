<script setup lang="ts">
  import { computed } from 'vue'
  import { pedalPercentLabel } from './hud-pedal-gauge'
  import { pedalPct } from './hud-rpm-segments'

  const props = withDefaults(
    defineProps<{
      label: 'THR' | 'BRK'
      value: number
      compact?: boolean
    }>(),
    { compact: false },
  )

  const pct = computed(() => pedalPct(props.value))
  const pctLabel = computed(() => pedalPercentLabel(props.value))
  const isThr = computed(() => props.label === 'THR')
</script>

<template>
  <div class="pedal" :class="[isThr ? 'thr' : 'brk', { compact }]">
    <div class="head">
      <span class="lbl">{{ label }}</span>
      <span class="val">{{ pctLabel }}</span>
    </div>
    <div
      class="track"
      role="meter"
      :aria-valuenow="Math.round(pct * 100)"
      aria-valuemin="0"
      aria-valuemax="100"
    >
      <div class="fill" :style="{ width: `${pct * 100}%` }" />
    </div>
  </div>
</template>

<style scoped>
  .pedal {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 64px;
  }

  .pedal.compact {
    min-width: 52px;
    gap: 2px;
  }

  .head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 6px;
  }

  .lbl {
    font-size: 8px;
    letter-spacing: 0.14em;
    font-weight: 700;
    color: rgba(148, 163, 184, 0.9);
  }

  .val {
    font-size: 10px;
    font-weight: 700;
    color: #f1f5f9;
  }

  .compact .val {
    font-size: 9px;
  }

  .track {
    height: 5px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 2px;
    overflow: hidden;
  }

  .compact .track {
    height: 4px;
  }

  .fill {
    height: 100%;
    border-radius: 2px;
    transition: width 75ms linear;
  }

  .thr .fill {
    background: #22c55e;
    box-shadow: 0 0 6px rgba(34, 197, 94, 0.45);
  }

  .brk .fill {
    background: #ef4444;
    box-shadow: 0 0 6px rgba(239, 68, 68, 0.45);
  }
</style>
