/** X positions for arc tach tick labels (viewBox 0 0 220 118). */
export const ARC_TACH_TICK_X = [24, 62, 110, 158, 196] as const

export const ARC_TACH_TICKS = ['0', '2', '4', '6', '8'] as const

export function arcTachTickX(index: number): number {
  return ARC_TACH_TICK_X[index] ?? 110
}
