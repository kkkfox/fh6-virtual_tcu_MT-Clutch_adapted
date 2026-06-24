export function pedalPercentLabel(value: number): string {
  const pct = Math.max(0, Math.min(1, value))
  return `${Math.round(pct * 100)}%`
}
