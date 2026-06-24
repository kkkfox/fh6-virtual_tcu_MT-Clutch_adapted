export const HUD_TEMPLATES = [
  { value: 'classic', i18nKey: 'hudClassic' },
  { value: 'racing', i18nKey: 'hudRacing' },
  { value: 'minimal', i18nKey: 'hudMinimal' },
] as const

export type HudTemplateId = (typeof HUD_TEMPLATES)[number]['value']

const VALID = new Set<string>(HUD_TEMPLATES.map((t) => t.value))

/** @deprecated glass removed — map saved configs to classic */
const LEGACY: Record<string, HudTemplateId> = { glass: 'classic' }

export function normalizeHudTemplate(value: unknown): HudTemplateId {
  if (typeof value === 'string') {
    if (VALID.has(value)) return value as HudTemplateId
    if (value in LEGACY) return LEGACY[value]!
  }
  return 'classic'
}

export type ShiftAdvice = 'up' | 'down' | ''

export function parseShiftAdvice(value: unknown): ShiftAdvice {
  if (value === 'up' || value === 'down') return value
  return ''
}

/** Minimum HUD window bounds per template (Electron overlay). Height is not capped — content drives it. */
export const HUD_TEMPLATE_LAYOUT: Record<
  HudTemplateId,
  {
    minWidth: number
    minHeight: number
    maxWidth: number
  }
> = {
  classic: { minWidth: 280, minHeight: 160, maxWidth: 340 },
  racing: { minWidth: 320, minHeight: 200, maxWidth: 440 },
  minimal: { minWidth: 340, minHeight: 100, maxWidth: 440 },
}

export function getHudTemplateLayout(template: HudTemplateId) {
  return HUD_TEMPLATE_LAYOUT[template] ?? HUD_TEMPLATE_LAYOUT.classic
}
