const COLORS: Record<string, string> = {
  high: 'badge-green',
  medium: 'badge-yellow',
  low: 'badge-orange',
  unavailable: 'badge-gray',
}

interface Props {
  level: string
  title?: string
}

export default function ConfidenceBadge({ level, title }: Props) {
  return (
    <span className={`badge ${COLORS[level] || 'badge-gray'}`} title={title}>
      {level}
    </span>
  )
}
