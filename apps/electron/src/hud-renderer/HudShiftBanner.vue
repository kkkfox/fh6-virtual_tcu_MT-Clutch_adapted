<script setup lang="ts">
  import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'
  import { toRef } from 'vue'
  import { useHudShiftBanner } from './hud-shift-banner'

  const props = withDefaults(
    defineProps<{
      advice?: ShiftAdvice
      show?: boolean
    }>(),
    {
      advice: '',
      show: false,
    },
  )

  const { isUp, isDown, label, chevLeft, chevRight } = useHudShiftBanner(
    toRef(props, 'advice'),
    toRef(props, 'show'),
  )
</script>

<template>
  <div
    class="shift-banner global-shift-banner"
    :class="{ active: isUp || isDown, up: isUp, down: isDown }"
    role="status"
    :aria-hidden="!(isUp || isDown)"
  >
    <span class="chev chev-l" aria-hidden="true">{{ chevLeft }}</span>
    <span class="label">{{ label }}</span>
    <span class="chev chev-r" aria-hidden="true">{{ chevRight }}</span>
  </div>
</template>

<style scoped>
  .shift-banner {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 8px;
    min-height: 28px;
    padding: 6px 14px;
    margin-top: 4px;
    border-radius: 0 0 8px 8px;
    opacity: 0.35;
    background: rgba(0, 0, 0, 0.35);
    border: 1px solid transparent;
    border-top: none;
    transition:
      opacity 180ms,
      background 180ms,
      border-color 180ms;
  }

  .shift-banner.active {
    opacity: 1;
    background: rgba(0, 0, 0, 0.55);
  }

  .shift-banner.up.active {
    border-top: 1px solid rgba(234, 179, 8, 0.35);
  }

  .shift-banner.down.active {
    border-top: 1px solid rgba(56, 189, 248, 0.35);
  }

  .chev {
    font-size: 14px;
    font-weight: 900;
    letter-spacing: -0.08em;
    color: rgba(234, 179, 8, 0.25);
    text-align: center;
    min-width: 28px;
  }

  .shift-banner.down .chev {
    color: rgba(56, 189, 248, 0.25);
  }

  .shift-banner.up.active .chev {
    color: #eab308;
    text-shadow: 0 0 8px rgba(234, 179, 8, 0.6);
    animation: chev-pulse 1s ease-in-out infinite;
  }

  .shift-banner.down.active .chev {
    color: #38bdf8;
    text-shadow: 0 0 8px rgba(56, 189, 248, 0.6);
    animation: chev-pulse 1s ease-in-out infinite;
  }

  .chev-l {
    text-align: right;
  }

  .chev-r {
    text-align: left;
  }

  .label {
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.2em;
    color: rgba(234, 179, 8, 0.35);
    white-space: nowrap;
  }

  .shift-banner.down .label {
    color: rgba(56, 189, 248, 0.35);
  }

  .shift-banner.up.active .label {
    color: #fde047;
  }

  .shift-banner.down.active .label {
    color: #7dd3fc;
  }

  @keyframes chev-pulse {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.55;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .shift-banner.active .chev {
      animation: none;
    }
  }
</style>
