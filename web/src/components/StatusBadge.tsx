interface Props {
  status: string
}

const COLORS: Record<string, string> = {
  integrated: 'badge-green',
  offline_parse_candidate: 'badge-yellow',
  parser_prototype_ready: 'badge-yellow',
  captured_browser: 'badge-blue',
  captured_static: 'badge-blue',
  discovered: 'badge-gray',
  deferred: 'badge-orange',
  rejected: 'badge-gray',
}

export default function StatusBadge({ status }: Props) {
  return <span className={`badge ${COLORS[status] || 'badge-gray'}`}>{status}</span>
}
