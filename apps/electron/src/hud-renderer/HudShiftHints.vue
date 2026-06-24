<script setup lang="ts">
  import type { ShiftAdvice } from '@virtual-tcu/shared/config/hud'

  withDefaults(
    defineProps<{
      advice?: ShiftAdvice
      show?: boolean
      size?: 'sm' | 'md' | 'lg'
      /** split: up above gear, down below; below: all hints under gear */
      placement?: 'split' | 'below'
    }>(),
    {
      advice: '',
      show: false,
      size: 'md',
      placement: 'split',
    },
  )
</script>

<template>
  <div class="shift-hints" :class="[`size-${size}`, `placement-${placement}`, { enabled: show }]">
    <template v-if="placement === 'split'">
      <div class="slot up" :class="{ active: show && advice === 'up' }" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M12 19V5M6 11l6-6 6 6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>

      <div class="gear-slot">
        <slot />
      </div>

      <div class="slot down" :class="{ active: show && advice === 'down' }" aria-hidden="true">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
          <path d="M12 5v14M6 13l6 6 6-6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
    </template>

    <template v-else>
      <div class="gear-slot">
        <slot />
      </div>

      <div
        class="slot below"
        :class="{
          active: show && (advice === 'up' || advice === 'down'),
          up: advice === 'up',
          down: advice === 'down',
        }"
        aria-hidden="true"
      >
        <svg
          v-if="show && advice === 'up'"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path d="M12 19V5M6 11l6-6 6 6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
        <svg
          v-else-if="show && advice === 'down'"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
        >
          <path d="M12 5v14M6 13l6 6 6-6" stroke-linecap="round" stroke-linejoin="round" />
        </svg>
      </div>
    </template>
  </div>
</template>

<style scoped>
  .shift-hints {
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .slot {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 14px;
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
  }

  .slot.below {
    height: 16px;
    margin-top: 1px;
  }

  .slot svg {
    width: 12px;
    height: 12px;
  }

  .size-md .slot {
    height: 16px;
  }

  .size-md .slot svg,
  .size-md .slot.below svg {
    width: 14px;
    height: 14px;
  }

  .size-lg .slot {
    height: 18px;
  }

  .size-lg .slot svg,
  .size-lg .slot.below svg {
    width: 16px;
    height: 16px;
  }

  .slot.up.active,
  .slot.below.up.active {
    opacity: 1;
    visibility: visible;
    color: #22c55e;
    filter: drop-shadow(0 0 5px rgba(34, 197, 94, 0.55));
    animation: pulse-up 1.1s ease-in-out infinite;
  }

  .slot.down.active,
  .slot.below.down.active {
    opacity: 1;
    visibility: visible;
    color: #eab308;
    filter: drop-shadow(0 0 5px rgba(234, 179, 8, 0.55));
    animation: pulse-down 1.1s ease-in-out infinite;
  }

  .gear-slot {
    display: flex;
    align-items: center;
    justify-content: center;
  }

  @keyframes pulse-up {
    0%,
    100% {
      opacity: 1;
      transform: translateY(0);
    }
    50% {
      opacity: 0.7;
      transform: translateY(-2px);
    }
  }

  @keyframes pulse-down {
    0%,
    100% {
      opacity: 1;
      transform: translateY(0);
    }
    50% {
      opacity: 0.7;
      transform: translateY(2px);
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .slot.active {
      animation: none;
    }
  }
</style>
