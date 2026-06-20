import { sourceManifest } from '../data/loader'
import StatusBadge from '../components/StatusBadge'
import type { SourceEntry } from '../data/types'

const CATEGORY_LABELS: Record<string, string> = {
  completed_player_trades: 'Completed Player Trades',
  cash_market: 'Cash Market',
  forum_reference: 'Forum Reference',
  community_discussion: 'Community Discussion',
  source_directory_only: 'Source Directory',
}

function SourceCard({ source }: { source: SourceEntry }) {
  const isIntegrated = source.status === 'integrated'
  const isCash = source.category === 'cash_market'
  const isDiablo2io = source.source_slug === 'diablo2_io'

  return (
    <div className={`source-card ${isIntegrated ? 'card-highlight' : ''}`}>
      <div className="source-card-header">
        <h3>{source.display_name}</h3>
        <StatusBadge status={source.status} />
      </div>

      <div className="source-card-meta">
        <span>Priority: <strong>{source.priority}</strong></span>
        <span>Category: <strong>{CATEGORY_LABELS[source.category] || source.category}</strong></span>
      </div>

      <div className="source-card-classes">
        {source.evidence_classes.map((cls) => (
          <span key={cls} className="evidence-tag">{cls}</span>
        ))}
      </div>

      {source.surfaces_checked && (
        <div className="surfaces-grid">
          {Object.entries(source.surfaces_checked).map(([key, val]) => (
            <span key={key} className={`surface-item surface-${val}`}>
              {key.replace(/_/g, ' ')}: {val}
            </span>
          ))}
        </div>
      )}

      {source.caveats.length > 0 && (
        <ul className="caveat-list">
          {source.caveats.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      )}

      <p className="source-next-action"><strong>Next:</strong> {source.next_action}</p>

      {isDiablo2io && (
        <div className="caveat-box">
          use_in_model=false — candidate evidence only. Not integrated into pricing.
        </div>
      )}
      {isCash && (
        <div className="caveat-box caveat-cash">
          Cash-market source — comparison only. Not used in in-game rune ratios.
        </div>
      )}
    </div>
  )
}

export default function Sources() {
  const categories = [...new Set(sourceManifest.map((s) => s.category))]
    .sort()
    .filter((c) => c !== 'source_directory_only')
  const directorySources = sourceManifest.filter((s) => s.category === 'source_directory_only')

  return (
    <div>
      <h1>Sources</h1>
      <p className="page-subtitle">Every source tracked in the D2R Market Helper source manifest, with status, evidence class, and caveats.</p>

      {categories.map((cat) => (
        <section key={cat}>
          <h2>{CATEGORY_LABELS[cat] || cat}</h2>
          <div className="source-list">
            {sourceManifest
              .filter((s) => s.category === cat)
              .map((s) => (
                <SourceCard key={s.source_slug} source={s} />
              ))}
          </div>
        </section>
      ))}

      {directorySources.length > 0 && (
        <section>
          <h2>Source Directory</h2>
          <div className="source-list">
            {directorySources.map((s) => (
              <SourceCard key={s.source_slug} source={s} />
            ))}
          </div>
        </section>
      )}
    </div>
  )
}
