import { useState, useMemo } from 'react'
import SegmentSelector from '../components/SegmentSelector'
import ConfidenceBadge from '../components/ConfidenceBadge'
import CashDisclaimer from '../components/CashDisclaimer'
import {
  type SegmentSlug,
  DEFAULT_SEGMENT,
  SEGMENT_LABELS,
} from '../data/types'
import { getSortedRunes, sourceManifest, externalCash } from '../data/loader'

function useSegment() {
  const params = new URLSearchParams(window.location.search)
  const initial = (params.get('segment') as SegmentSlug) || DEFAULT_SEGMENT
  const [seg, setSeg] = useState<SegmentSlug>(initial)

  const update = (s: SegmentSlug) => {
    setSeg(s)
    const url = new URL(window.location.href)
    url.searchParams.set('segment', s)
    window.history.replaceState({}, '', url.toString())
  }

  return [seg, update] as const
}

export default function Home() {
  const [segment, setSegment] = useSegment()
  const runes = useMemo(() => getSortedRunes(segment), [segment])

  const integratedSources = sourceManifest.filter((s) => s.status === 'integrated')
  const cashSources = sourceManifest.filter((s) => s.category === 'cash_market' && s.status !== 'deferred')

  const topRunes = runes.filter((r) => r.confidence !== 'unavailable').slice(0, 8)
  const observationCount = runes.filter((r) => r.confidence !== 'unavailable').length
  const totalTrades = runes.reduce((sum, r) => sum + (r.total_trades || 0), 0)

  return (
    <div>
      <h1>Market Overview</h1>
      <SegmentSelector value={segment} onChange={setSegment} />

      <div className="snapshot-grid">
        <div className="snapshot-card">
          <div className="snapshot-label">Segment</div>
          <div className="snapshot-value">{SEGMENT_LABELS[segment]}</div>
        </div>
        <div className="snapshot-card">
          <div className="snapshot-label">Runes Priced</div>
          <div className="snapshot-value">{observationCount}<span className="snapshot-sub"> / 23 tracked</span></div>
        </div>
        <div className="snapshot-card">
          <div className="snapshot-label">Modeled Trades</div>
          <div className="snapshot-value">{totalTrades.toLocaleString()}</div>
        </div>
        <div className="snapshot-card">
          <div className="snapshot-label">Primary Source</div>
          <div className="snapshot-value">Traderie</div>
          <div className="snapshot-sub">Completed trades</div>
        </div>
      </div>

      <h2>Top Runes by Volume</h2>
      <div className="rune-mini-grid">
        {topRunes.map((r) => (
          <div key={r.rune} className="rune-mini-card">
            <div className="rune-mini-name">{r.rune.replace(' Rune', '')}</div>
            <div className="rune-mini-value">
              {r.value_ist !== null ? `${r.value_ist.toFixed(2)} Ist` : '—'}
            </div>
            <div className="rune-mini-meta">
              {r.total_trades} trades · <ConfidenceBadge level={r.confidence} />
            </div>
          </div>
        ))}
      </div>

      <h2>External Cash Comparison</h2>
      <CashDisclaimer />
      <div className="cash-mini-list">
        {externalCash?.observations?.slice(0, 6).map((obs, i) => (
          <div key={i} className="cash-mini-row">
            <span className="cash-mini-item">{obs.item_name}</span>
            <span className="cash-mini-price">${obs.unit_price?.toFixed(2) ?? '—'}</span>
            <span className="cash-mini-source">{obs.source_slug}</span>
          </div>
        ))}
      </div>

      <h2>Source Directory</h2>
      <div className="source-summary-grid">
        {integratedSources.concat(cashSources.slice(0, 4)).map((s) => (
          <div key={s.source_slug} className="source-summary-card">
            <div className="source-summary-name">{s.display_name}</div>
            <div className="source-summary-status">{s.status}</div>
            <div className="source-summary-priority">{s.priority}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
