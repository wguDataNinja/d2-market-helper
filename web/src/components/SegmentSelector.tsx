import { ALL_SEGMENTS, SEGMENT_LABELS, type SegmentSlug } from '../data/types'

interface Props {
  value: SegmentSlug
  onChange: (s: SegmentSlug) => void
}

export default function SegmentSelector({ value, onChange }: Props) {
  return (
    <div className="segment-selector">
      <label>Economy Segment:</label>
      <select value={value} onChange={(e) => onChange(e.target.value as SegmentSlug)}>
        {ALL_SEGMENTS.map((s) => (
          <option key={s} value={s}>
            {SEGMENT_LABELS[s]}
          </option>
        ))}
      </select>
    </div>
  )
}
