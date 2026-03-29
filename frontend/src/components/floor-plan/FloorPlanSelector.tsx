import type { FloorPlan } from '../../types'

interface FloorPlanSelectorProps {
  floorPlans: FloorPlan[]
  selectedId: number | null
  onChange: (id: number | null) => void
  isLoading?: boolean
}

export function FloorPlanSelector({
  floorPlans,
  selectedId,
  onChange,
  isLoading = false,
}: FloorPlanSelectorProps) {
  const activeFloorPlans = floorPlans.filter((fp) => fp.is_active)

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="floor-plan-select" className="text-sm font-medium text-gray-700">
        Floor Plan:
      </label>
      <select
        id="floor-plan-select"
        value={selectedId ?? ''}
        onChange={(e) => onChange(e.target.value ? Number(e.target.value) : null)}
        className="px-3 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 bg-white"
        disabled={isLoading}
      >
        <option value="">Select a floor plan</option>
        {activeFloorPlans.map((fp) => (
          <option key={fp.id} value={fp.id}>
            {fp.name}
          </option>
        ))}
      </select>
      {isLoading && (
        <span className="text-sm text-gray-500">Loading...</span>
      )}
    </div>
  )
}
