import type {
  InGameRuneValues,
  ExternalCashPrices,
  SourceEntry,
  RuneRegistryEntry,
  SegmentSlug,
  RuneObservation,
  CashObservation,
} from './types'

import inGameValuesRaw from '@data/products/in_game_rune_values.json'
import traderieToolsRaw from '@data/products/traderie_tools_prices.json'
import externalCashRaw from '@data/products/external_cash_prices.sample.json'
import sourceManifestRaw from '@data/source_manifest.json'
import runeRegistryRaw from '@data/rune_registry.json'

export const inGameValues = inGameValuesRaw as unknown as InGameRuneValues
export const traderieTools = traderieToolsRaw
export const externalCash = externalCashRaw as unknown as ExternalCashPrices
export const sourceManifest = sourceManifestRaw as unknown as SourceEntry[]
export const runeRegistry = runeRegistryRaw as unknown as RuneRegistryEntry[]

export function getSegmentData(segment: SegmentSlug): Record<string, RuneObservation> {
  return inGameValues.segments?.[segment]?.runes || {}
}

export function getRuneObservations(segment: SegmentSlug): RuneObservation[] {
  const data = getSegmentData(segment)
  return Object.entries(data).map(([rune, obs]) => ({ ...obs, rune }))
}

export function getCashPrice(itemName: string): CashObservation | undefined {
  if (!externalCash?.observations) return undefined
  const normalized = itemName.toLowerCase().replace(' rune', '').trim()
  return externalCash.observations.find(
    (o) => o.normalized_item_name.toLowerCase() === normalized
  )
}

export function getCashPricesForRune(runeShortName: string): CashObservation[] {
  if (!externalCash?.observations) return []
  const normalized = runeShortName.toLowerCase().replace(' rune', '').trim()
  return externalCash.observations.filter(
    (o) => o.normalized_item_name.toLowerCase() === normalized
  )
}

export function getAllCashObservationsGrouped(): Record<string, CashObservation[]> {
  if (!externalCash?.observations) return {}
  const groups: Record<string, CashObservation[]> = {}
  for (const obs of externalCash.observations) {
    const key = obs.normalized_item_name.toLowerCase()
    if (!groups[key]) groups[key] = []
    groups[key].push(obs)
  }
  return groups
}

export type RuneRow = RuneObservation & { order: number; tier: string; cashPrices: CashObservation[] }

export function getSortedRunes(segment: SegmentSlug): RuneRow[] {
  const observations = getRuneObservations(segment)
  const registryMap = new Map(runeRegistry.map((r) => [r.short_name.toLowerCase(), r]))
  const cashGroups = getAllCashObservationsGrouped()

  return observations
    .map((obs) => {
      const key = obs.rune.toLowerCase().replace(' rune', '')
      const reg = registryMap.get(key)
      const cashPrices = cashGroups[key] || []
      return {
        ...obs,
        order: reg?.id ?? 99,
        tier: reg?.tier ?? 'unknown',
        cashPrices,
      }
    })
    .sort((a, b) => a.order - b.order)
}

export function getSourceBySlug(slug: string): SourceEntry | undefined {
  return sourceManifest.find((s) => s.source_slug === slug)
}

export function getGeneratedAt(): string {
  return inGameValues.generated_at
}

export function getProductGeneratedAt(): string {
  return inGameValues.product_generated_at
}

export function getSourceWindowLabel(): string {
  return inGameValues.source_window_label
}
