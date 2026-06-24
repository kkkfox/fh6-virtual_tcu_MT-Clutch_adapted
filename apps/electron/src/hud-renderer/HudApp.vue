<script setup lang="ts">
  import { computed } from 'vue'
  import { HUD_TEMPLATE_COMPONENTS } from './hud-templates'
  import { useHudApp } from './HudApp'
  import HudShiftBanner from './HudShiftBanner.vue'
  import './hud-shell.css'

  const {
    connected,
    hudTemplate,
    shellClass,
    clickThrough,
    hudProps,
    close,
    toggleClickThrough,
    syncClickThroughMouse,
  } = useHudApp()

  const activeTemplate = computed(
    () => HUD_TEMPLATE_COMPONENTS[hudTemplate.value] ?? HUD_TEMPLATE_COMPONENTS.classic,
  )
</script>

<template>
  <div class="hud-frame">
    <div
      class="hud-root"
      :class="[
        shellClass,
        hudTemplate,
        { disconnected: !connected, 'click-through': clickThrough },
      ]"
      @mousemove="syncClickThroughMouse"
      @mouseenter="syncClickThroughMouse"
    >
      <component
        :is="activeTemplate"
        v-bind="hudProps"
        @toggle-click-through="toggleClickThrough"
        @close="close"
      />
      <HudShiftBanner v-if="hudProps.showShiftBanner" :advice="hudProps.shiftAdvice" show />
    </div>
  </div>
</template>

<style scoped>
  .hud-frame {
    width: fit-content;
    height: fit-content;
    box-sizing: border-box;
  }

  .hud-root {
    display: flex;
    flex-direction: column;
    gap: 0;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .hud-root :deep(.global-shift-banner) {
    margin-top: 0;
    border-radius: 0 0 11px 11px;
  }

  .hud-root.tpl-minimal-shell :deep(.global-shift-banner) {
    border-radius: 0 0 8px 8px;
  }

  .hud-root.tpl-classic-shell {
    --hud-min-width: 280px;
    --hud-max-width: 320px;
    background: rgba(0, 0, 0, 0.88);
    border-color: rgba(255, 255, 255, 0.12);
    border-radius: 14px;
    color: #f8fafc;
  }

  .hud-root.tpl-minimal-shell {
    --hud-min-width: 340px;
    --hud-max-width: 420px;
    --hud-pad-x: 4px;
    --hud-pad-y: 4px;
    background: transparent;
    border: none;
    border-radius: 0;
  }

  .hud-root.tpl-racing-shell {
    --hud-min-width: 320px;
    --hud-max-width: 400px;
    --hud-pad-x: 12px;
    --hud-pad-y: 10px;
    background: rgba(0, 0, 0, 0.9);
    border-color: rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    color: #f8fafc;
  }

  .hud-root.click-through.tpl-classic-shell .gear,
  .hud-root.click-through.tpl-minimal-shell .gear,
  .hud-root.click-through.tpl-racing-shell .gear,
  .hud-root.click-through .speed,
  .hud-root.click-through .speed-line,
  .hud-root.click-through .val {
    -webkit-text-stroke: 2px rgba(0, 0, 0, 0.9);
    paint-order: stroke fill;
  }
</style>
