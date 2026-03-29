interface StatusBadgeProps {
  isOnline: boolean
}

export function StatusBadge({ isOnline }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
        isOnline
          ? 'bg-green-100 text-green-800'
          : 'bg-red-100 text-red-800'
      }`}
    >
      <span
        className={`w-1.5 h-1.5 rounded-full ${
          isOnline ? 'bg-green-500' : 'bg-red-500'
        }`}
      />
      {isOnline ? 'Online' : 'Offline'}
    </span>
  )
}
