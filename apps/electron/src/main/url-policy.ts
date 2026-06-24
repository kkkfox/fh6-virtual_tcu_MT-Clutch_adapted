/**
 * Restrict renderer-initiated external links (SSRF / local redirect hardening).
 */

import { isIP } from 'node:net'
import { shell } from 'electron'

function stripIpv6Brackets(hostname: string): string {
  return hostname.replace(/^\[|\]$/g, '')
}

function isPrivateIpv4(a: number, b: number): boolean {
  if (a === 127 || a === 0) return true
  if (a === 10) return true
  if (a === 172 && b >= 16 && b <= 31) return true
  if (a === 192 && b === 168) return true
  if (a === 169 && b === 254) return true
  return false
}

function extractIpv4FromMappedV6(host: string): string | null {
  const prefix = '::ffff:'
  if (!host.startsWith(prefix)) return null

  const tail = host.slice(prefix.length)
  if (tail.includes('.')) {
    return isIP(tail) === 4 ? tail : null
  }

  const parts = tail.split(':')
  if (parts.length !== 2) return null

  const hi = Number.parseInt(parts[0], 16)
  const lo = Number.parseInt(parts[1], 16)
  if (
    !Number.isFinite(hi) ||
    !Number.isFinite(lo) ||
    hi < 0 ||
    hi > 0xffff ||
    lo < 0 ||
    lo > 0xffff
  ) {
    return null
  }

  return `${(hi >> 8) & 0xff}.${hi & 0xff}.${(lo >> 8) & 0xff}.${lo & 0xff}`
}

function isPrivateIpv6(host: string): boolean {
  const h = host.toLowerCase()
  if (h === '::1') return true
  if (h.startsWith('fe80:')) return true
  if (h.startsWith('fc') || h.startsWith('fd')) return true

  const mappedIpv4 = extractIpv4FromMappedV6(h)
  if (mappedIpv4) {
    const parts = mappedIpv4.split('.').map((p) => Number(p))
    return isPrivateIpv4(parts[0], parts[1])
  }

  return false
}

export function isBlockedExternalHost(hostname: string): boolean {
  const host = stripIpv6Brackets(hostname).toLowerCase()
  if (!host) return true
  if (host === 'localhost' || host.endsWith('.localhost') || host.endsWith('.local')) {
    return true
  }

  const ipKind = isIP(host)
  if (ipKind === 4) {
    const parts = host.split('.').map((p) => Number(p))
    if (parts.length !== 4 || parts.some((n) => !Number.isInteger(n) || n < 0 || n > 255)) {
      return true
    }
    return isPrivateIpv4(parts[0], parts[1])
  }
  if (ipKind === 6) return isPrivateIpv6(host)

  return false
}

export function isAllowedExternalUrl(raw: string): boolean {
  try {
    const parsed = new URL(raw)
    if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') return false
    if (parsed.username || parsed.password) return false
    return !isBlockedExternalHost(parsed.hostname)
  } catch {
    return false
  }
}

export async function openExternalUrl(url: string): Promise<{ ok: boolean; error?: string }> {
  if (!isAllowedExternalUrl(url)) {
    console.warn('[main] openExternal blocked:', url)
    return { ok: false, error: 'URL is not allowed' }
  }

  try {
    await shell.openExternal(new URL(url).href)
    return { ok: true }
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err)
    console.error('[main] openExternal failed:', message)
    return { ok: false, error: message }
  }
}
