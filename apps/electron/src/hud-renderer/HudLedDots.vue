<script setup lang="ts">
  import { computed } from 'vue'
  import { buildLedDots } from './hud-rpm-segments'

  const props = withDefaults(defineProps<{ rpmPct: number; count?: number }>(), { count: 16 })

  const dots = computed(() => buildLedDots(props.rpmPct, props.count))
</script>

<template>
  <div
    class="led-dots"
    role="meter"
    :aria-valuenow="Math.round(rpmPct * 100)"
    aria-valuemin="0"
    aria-valuemax="100"
  >
    <span v-for="(d, i) in dots" :key="i" class="dot" :class="[d.tone, { lit: d.lit }]" />
  </div>
</template>

<style scoped>
  .led-dots {
    display: flex;
    gap: 4px;
    justify-content: center;
    align-items: center;
    padding: 4px 0;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.12);
    transition:
      background 80ms linear,
      box-shadow 80ms linear;
  }

  .dot.lit.live {
    background: #22c55e;
    box-shadow: 0 0 6px rgba(34, 197, 94, 0.55);
  }

  .dot.lit.warn {
    background: #eab308;
    box-shadow: 0 0 5px rgba(234, 179, 8, 0.5);
  }

  .dot.red:not(.lit) {
    background: rgba(239, 68, 68, 0.25);
  }

  .dot.lit.red {
    background: #ef4444;
    box-shadow: 0 0 6px rgba(239, 68, 68, 0.55);
  }
</style>
