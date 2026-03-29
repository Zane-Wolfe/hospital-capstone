interface BatteryIndicatorProps {
  percent: number | null
}

export function BatteryIndicator({ percent }: BatteryIndicatorProps) {
  if (percent === null) {
    return <span className="text-gray-400 text-sm">--</span>
  }

  const getColor = () => {
    if (percent < 20) return 'bg-red-500'
    if (percent < 50) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getTextColor = () => {
    if (percent < 20) return 'text-red-600'
    if (percent < 50) return 'text-yellow-600'
    return 'text-green-600'
  }

  return (
    <div className="flex items-center gap-2">
      <div className="w-8 h-4 border border-gray-300 rounded-sm relative">
        <div
          className={`absolute left-0 top-0 bottom-0 ${getColor()} rounded-sm transition-all`}
          style={{ width: `${percent}%` }}
        />
        <div className="absolute -right-1 top-1/2 -translate-y-1/2 w-0.5 h-2 bg-gray-300 rounded-r" />
      </div>
      <span className={`text-sm font-medium ${getTextColor()}`}>
        {percent}%
      </span>
    </div>
  )
}
