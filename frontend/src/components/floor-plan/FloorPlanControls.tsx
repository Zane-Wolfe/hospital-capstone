interface FloorPlanControlsProps {
  scale: number
  onZoomIn: () => void
  onZoomOut: () => void
  onReset: () => void
  mode: 'view' | 'edit'
  onModeChange: (mode: 'view' | 'edit') => void
}

export function FloorPlanControls({
  scale,
  onZoomIn,
  onZoomOut,
  onReset,
  mode,
  onModeChange,
}: FloorPlanControlsProps) {
  return (
    <div className="absolute top-4 right-4 flex flex-col gap-2 bg-white rounded-lg shadow-lg p-2">
      <div className="flex gap-1">
        <button
          onClick={onZoomIn}
          className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-lg font-bold"
          title="Zoom in"
        >
          +
        </button>
        <button
          onClick={onZoomOut}
          className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-lg font-bold"
          title="Zoom out"
        >
          -
        </button>
        <button
          onClick={onReset}
          className="px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded text-sm"
          title="Reset view"
        >
          Reset
        </button>
      </div>
      <div className="text-xs text-center text-gray-500">{Math.round(scale * 100)}%</div>
      <div className="border-t pt-2">
        <div className="flex gap-1">
          <button
            onClick={() => onModeChange('view')}
            className={`px-2 py-1 text-xs rounded ${
              mode === 'view'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            View
          </button>
          <button
            onClick={() => onModeChange('edit')}
            className={`px-2 py-1 text-xs rounded ${
              mode === 'edit'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 hover:bg-gray-200'
            }`}
          >
            Edit
          </button>
        </div>
      </div>
    </div>
  )
}
