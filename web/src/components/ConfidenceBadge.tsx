const COLORS: Record<string, string> = {
  high: 'badge-green',
  medium: 'badge-yellow',
  low: 'badge-orange',
  unavailable: 'badge-gray',
}

interface Props {
  level: string
}

export default function ConfidenceBadge({ level }: Props) {
  return <span className={`badge ${COLORS[level] || 'badge-gray'}`}>{level}</span>
}
