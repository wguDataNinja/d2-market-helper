export default function Methodology() {
  return (
    <div>
      <h1>Methodology</h1>
      <p className="page-subtitle">
        How D2R Market Helper sources, classifies, and presents trade data. This page documents
        every rule that governs what you see and what you should not infer.
      </p>

      <section className="methodology-section">
        <h2>In-Game Values vs Cash Prices Are Separate</h2>
        <p>
          In-game rune values are derived from <strong>completed player trades</strong> on Traderie.
          Cash prices come from external real-money marketplace listings. These are fundamentally
          different markets and are <strong>never blended</strong>.
        </p>
        <p>
          Cash prices are seller asking prices, not completed sales. They include seller margin,
          delivery risk, site fees, and stock constraints. The project always displays them in
          separate visual columns with explicit labels.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Economy Segments Are Not Merged</h2>
        <p>
          D2R has separate economies by platform (PC), ladder status (Ladder / Non-Ladder),
          and difficulty (Softcore / Hardcore). The project tracks four minimum PC segments:
        </p>
        <ul>
          <li><strong>pc_sc_l</strong> — PC Softcore Ladder</li>
          <li><strong>pc_sc_nl</strong> — PC Softcore Non-Ladder</li>
          <li><strong>pc_hc_l</strong> — PC Hardcore Ladder</li>
          <li><strong>pc_hc_nl</strong> — PC Hardcore Non-Ladder</li>
        </ul>
        <p>
          These segments are never merged. Each price is tied to its segment. Cross-segment
          aggregation would hide real market differences.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Primary Source: Traderie Completed Trades</h2>
        <p>
          The in-game rune ratio model currently uses <strong>Traderie completed trades</strong> as its
          sole source. Rune-for-rune completed trades are extracted, normalized to Ist, and
          priced via bid/ask VWAP.
        </p>
        <p>
          Only rune-for-rune trades are modeled. AND trades (multiple runes on one side) are
          extracted but not yet priced. Active listings are not used.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Diablo2.io: Candidate Evidence Only</h2>
        <p>
          Diablo2.io has a sold-trade search surface (<code>activesold=1</code>) that exposes
          completed WTS/WTB rows with seller, buyer, and accepted consideration. However:
        </p>
        <ul>
          <li>Parser validation is not yet complete.</li>
          <li>Row semantics (actual vs claimed sold status) need verification.</li>
          <li>Segment filter parsing from HTML is not yet automated.</li>
        </ul>
        <p>
          <strong>Diablo2.io observations are not used in the pricing model</strong>. They are
          research-only until validation is complete.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Active Listings Are Not Completed Trades</h2>
        <p>
          Active listings (browsetrades.php on Diablo2.io, or unfiltered Traderie listings)
          represent asking prices or trade offers, not actual completed transactions.
          The project does not use active listings as price evidence.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Confidence Is Volume-Based</h2>
        <p>
          Each rune observation in each segment gets a confidence label based on trade count:
        </p>
        <ul>
          <li><strong>High:</strong> 50+ trades</li>
          <li><strong>Medium:</strong> 15-49 trades</li>
          <li><strong>Low:</strong> 1-14 trades</li>
          <li><strong>Unavailable:</strong> 0 trades (no price)</li>
        </ul>
        <p>
          Thin-volume segments (Hardcore Non-Ladder: 5 trades total) produce mostly
          <strong>unavailable</strong> or <strong>low</strong> confidence observations.
          This is displayed honestly rather than hidden.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Game Version / Ruleset</h2>
        <p>
          D2R has three game versions: <strong>Classic</strong>,{' '}
          <strong>Lord of Destruction</strong>, and{' '}
          <strong>Reign of the Warlock</strong>. Each listing on Traderie carries a
          Game version property in its metadata.
        </p>
        <p>
          The project tracks Game version for every completed trade observation,
          but <strong>does not split prices by ruleset</strong>. As of the latest
          data audit, Reign of the Warlock (ROTW) constitutes <strong>over 95%
          </strong> of observed completed trades across all tracked segments.
          Lord of Destruction and Classic listings have insufficient volume for
          separate VWAP pricing. Prices shown are aggregate across all game versions
          within each segment.
        </p>
        <p>
          The <code>ruleset_breakdown</code> metadata in the product JSON shows
          exact observed counts by game version per segment.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Region Is Not Available in Completed-Trades Data</h2>
        <p>
          The Traderie website UI shows a Region filter (Americas / Europe / Asia)
          for active listings. However, the <strong>completed-trades API does not
          expose region data</strong>. Every completed trade observation is
          region-agnostic. This is a structural limitation of the data source.
        </p>
      </section>

      <section className="methodology-section">
        <h2>Known Limitations</h2>
        <ul>
          <li>Traderie is an unofficial API surface — behavior may change.</li>
          <li>Pagination/window behavior of the completed trades endpoint is not fully understood.</li>
          <li>No buyer metadata is exposed by Traderie completed trades.</li>
          <li>Only rune-for-rune trades are modeled (AND trades excluded from VWAP).</li>
          <li>Game versions are not split — prices aggregate Classic, LoD, and ROTW (ROTW dominates).</li>
          <li>Region data is unavailable for completed trades — only visible on the website UI.</li>
          <li>Hardcore segments have thin volume.</li>
          <li>Diablo2.io parser is not yet validated.</li>
          <li>Cash sources are asking prices, not completed sales.</li>
          <li>External cash prices may differ from actual market rates due to fees, stock, and delivery costs.</li>
        </ul>
      </section>

      <section className="methodology-section">
        <h2>Every Number on This Site Is Tied To</h2>
        <ol>
          <li>Its economy <strong>segment</strong></li>
          <li>Its <strong>source</strong> (and whether that source is integrated or candidate-only)</li>
          <li>Its <strong>evidence class</strong> (completed trade, listing, cash asking price, qualitative)</li>
          <li>Its <strong>confidence</strong> level and any applicable caveats</li>
        </ol>
        <p>
          If any of these four attributes is missing from a displayed number, that is a bug.
        </p>
      </section>
    </div>
  )
}
