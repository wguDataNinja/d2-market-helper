import { useState, useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import SegmentSelector from '../components/SegmentSelector'
import ConfidenceBadge from '../components/ConfidenceBadge'
import CashDisclaimer from '../components/CashDisclaimer'
import { type SegmentSlug, DEFAULT_SEGMENT } from '../data/types'
import { getSortedRunes } from '../data/loader'

export default function Runes() {
  const [searchParams, setSearchParams] = useSearchParams()
  const seg = (searchParams.get('segment') as SegmentSlug) || DEFAULT_SEGMENT

  const setSegment = (s: SegmentSlug) => {
    setSearchParams({ segment: s })
  }

  const [sortBy, setSortBy] = useState<'order' | 'value'>('order')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  const runes = useMemo(() => {
    const data = getSortedRunes(seg)
    return [...data].sort((a, b) => {
      if (sortBy === 'order') {
        return sortDir === 'asc' ? a.order - b.order : b.order - a.order
      }
      const av = a.value_ist ?? 0
      const bv = b.value_ist ?? 0
      return sortDir === 'asc' ? av - bv : bv - av
    })
  }, [seg, sortBy, sortDir])

  const toggleSort = (field: 'order' | 'value') => {
    if (sortBy === field) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    } else {
      setSortBy(field)
      setSortDir(field === 'value' ? 'desc' : 'asc')
    }
  }

  const sortArrow = (field: 'order' | 'value') => {
    if (sortBy !== field) return ''
    return sortDir === 'asc' ? ' ▲' : ' ▼'
  }

  return (
    <div>
      <h1>Rune Dashboard</h1>
      <SegmentSelector value={seg} onChange={setSegment} />

      <div className="caveat-box">
        <strong>In-game values</strong> are derived from Traderie completed trades using Ist-normalized VWAP.
        <br />
        <strong>Cash prices</strong> are external comparison only. Never blend in-game and cash prices.
      </div>

      <div className="table-controls">
        <button onClick={() => toggleSort('order')} className="btn-sort">
          Sort by Rune Order{sortArrow('order')}
        </button>
        <button onClick={() => toggleSort('value')} className="btn-sort">
          Sort by Ist Value{sortArrow('value')}
        </button>
      </div>

      <div className="table-wrapper">
        <table className="rune-table">
          <thead>
            <tr>
              <th>Rune</th>
              <th>Tier</th>
              <th className="num">Ist Value</th>
              <th className="num">Bid</th>
              <th className="num">Ask</th>
              <th className="num">Trades</th>
              <th>Confidence</th>
              <th className="num">Cash ($)</th>
              <th>Source</th>
            </tr>
          </thead>
          <tbody>
            {runes.length === 0 && (
              <tr>
                <td colSpan={9} className="empty-row">
                  No data available for this segment.
                </td>
              </tr>
            )}
            {runes.map((r) => (
              <tr key={r.rune} className={r.confidence === 'unavailable' ? 'row-unav' : ''}>
                <td className="rune-name">{r.rune.replace(' Rune', '')}</td>
                <td><span className={`tier-${r.tier}`}>{r.tier}</span></td>
                <td className="num">{r.value_ist !== null ? r.value_ist.toFixed(2) : '—'}</td>
                <td className="num">{r.bid_price !== null ? r.bid_price.toFixed(2) : '—'}</td>
                <td className="num">{r.ask_price !== null ? r.ask_price.toFixed(2) : '—'}</td>
                <td className="num">{r.total_trades || '—'}</td>
                <td><ConfidenceBadge level={r.confidence} /></td>
                <td className="num cash-cell">
                  {r.cashPrice ? `$${r.cashPrice.unit_price?.toFixed(2)}` : '—'}
                </td>
                <td className="source-cell">Traderie{r.cashPrice ? ` / ${r.cashPrice.source_slug}` : ''}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <CashDisclaimer />
    </div>
  )
}
