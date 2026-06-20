export type SegmentSlug = 'pc_sc_l' | 'pc_sc_nl' | 'pc_hc_l' | 'pc_hc_nl'

export const ALL_SEGMENTS: SegmentSlug[] = ['pc_sc_l', 'pc_sc_nl', 'pc_hc_l', 'pc_hc_nl']

export const SEGMENT_LABELS: Record<SegmentSlug, string> = {
  pc_sc_l: 'PC Softcore Ladder',
  pc_sc_nl: 'PC Softcore Non-Ladder',
  pc_hc_l: 'PC Hardcore Ladder',
  pc_hc_nl: 'PC Hardcore Non-Ladder',
}

export const DEFAULT_SEGMENT: SegmentSlug = 'pc_sc_nl'

export interface RuneObservation {
  rune: string
  value_ist: number | null
  bid_price: number | null
  ask_price: number | null
  bid_count: number
  ask_count: number
  total_trades: number
  confidence: 'high' | 'medium' | 'low' | 'unavailable'
  confidence_reason?: string
}

export interface InGameRuneValues {
  segments: Record<string, {
    segment_slug: string
    runes: Record<string, RuneObservation>
  }>
}

export interface RuneRegistryEntry {
  id: number
  name: string
  short_name: string
  tier: 'low' | 'medium' | 'high'
  names: {
    in_game: string
    traderie_tools: string
    cash: string
    cash_slug: string
  }
}

export interface CashObservation {
  source_slug: string
  item_name: string
  unit_price: number | null
  price_usd: number | null
  currency: string
  source_url: string
  caveats: string[]
  platform: string
  ladder: boolean
  hardcore: boolean
  softcore: boolean
  season_or_ruleset: string
}

export interface ExternalCashPrices {
  observations: CashObservation[]
}

export interface SourceEntry {
  source_slug: string
  display_name: string
  base_url: string
  category: string
  priority: string
  status: string
  use_in_model?: boolean
  evidence_classes: string[]
  surfaces_checked?: Record<string, string>
  segment_filters: Record<string, boolean | string>
  caveats: string[]
  next_action: string
  last_reviewed_at: string
}
