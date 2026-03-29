import { useState, useEffect, useCallback, useRef } from 'react'
import { useFloorPlans } from '../hooks/useFloorPlans'
import { useDevicePositions } from '../hooks/useDevicePositions'
import { useDeviceMetrics } from '../hooks/useDeviceMetrics'
import { useHeatmapData } from '../hooks/useHeatmapData'
import { useDateRange } from '../hooks/useDateRange'
import { useWebSocket } from '../hooks/useWebSocket'
import {
  FloorPlanCanvas,
  FloorPlanSelector,
  FloorPlanUpload,
  DeviceDetailModal,
  DevicePositionForm,
} from '../components/floor-plan'
import { DateRangePicker } from '../components/charts/DateRangePicker'
import { getFloorPlanImageUrl } from '../api/floorPlans'
import type { Sensor } from '../types'

export function LiveDataPage() {
  const { floorPlans, isLoading: plansLoading, create: createFloorPlan } = useFloorPlans()
  const [selectedFloorPlanId, setSelectedFloorPlanId] = useState<number | null>(null)
  const [mode, setMode] = useState<'view' | 'edit'>('view')
  const [isLive, setIsLive] = useState(true)
  const [heatmapMetric, setHeatmapMetric] = useState<'count' | 'db'>('count')
  const [showHeatmap, setShowHeatmap] = useState(true)
  const [showUploadDialog, setShowUploadDialog] = useState(false)
  const [showAddDeviceDialog, setShowAddDeviceDialog] = useState(false)
  const [selectedDeviceId, setSelectedDeviceId] = useState<string | null>(null)
  const [containerSize, setContainerSize] = useState({ width: 800, height: 600 })
  const containerRef = useRef<HTMLDivElement>(null)

  const { dateRange, setPreset, setCustomRange, timeRangeString } = useDateRange('1h')

  const selectedFloorPlan = floorPlans.find((fp) => fp.id === selectedFloorPlanId)

  const { positions, update: updatePosition, create: createPosition } = useDevicePositions(
    selectedFloorPlanId ?? undefined
  )
  const { metrics } = useDeviceMetrics()
  const { data: heatmapData, refetch: refetchHeatmap } = useHeatmapData({
    floorPlanId: selectedFloorPlanId,
    timeRange: isLive ? '-5m' : timeRangeString,
    metric: heatmapMetric,
  })

  // WebSocket for live updates - refetch heatmap when new events arrive
  useWebSocket({
    onEvent: useCallback(() => {
      if (isLive) {
        refetchHeatmap()
      }
    }, [refetchHeatmap, isLive]),
  })

  // Auto-select first floor plan
  useEffect(() => {
    if (!selectedFloorPlanId && floorPlans.length > 0) {
      const activePlan = floorPlans.find((fp) => fp.is_active)
      if (activePlan) {
        setSelectedFloorPlanId(activePlan.id)
      }
    }
  }, [floorPlans, selectedFloorPlanId])

  // Container size observer
  useEffect(() => {
    if (!containerRef.current) return

    const resizeObserver = new ResizeObserver((entries) => {
      const entry = entries[0]
      if (entry) {
        setContainerSize({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        })
      }
    })

    resizeObserver.observe(containerRef.current)
    return () => resizeObserver.disconnect()
  }, [])

  const handleDeviceDragEnd = async (sensorId: string, x: number, y: number) => {
    await updatePosition(sensorId, { x_coord: x, y_coord: y })
  }

  const handleDeviceClick = (sensorId: string) => {
    setSelectedDeviceId(sensorId)
  }

  const handleUpload = async (name: string, file: File, description?: string) => {
    const newPlan = await createFloorPlan(name, file, description)
    setSelectedFloorPlanId(newPlan.id)
    setShowUploadDialog(false)
  }

  const handleAddDevice = async (sensorId: string, x: number, y: number, label?: string) => {
    if (!selectedFloorPlanId) return
    await createPosition({
      sensor_id: sensorId,
      floor_plan_id: selectedFloorPlanId,
      x_coord: x,
      y_coord: y,
      label,
    })
    setShowAddDeviceDialog(false)
  }

  // Mock sensors for device form (in real app, fetch from sensors endpoint)
  const availableSensors: Sensor[] = metrics.map((m) => ({
    sensor_id: m.sensor_id,
    location: m.location || '',
    last_seen: m.last_heartbeat,
    event_count: 0,
  }))

  const existingSensorIds = positions.map((p) => p.sensor_id)

  const selectedPosition = positions.find((p) => p.sensor_id === selectedDeviceId)
  const selectedMetrics = metrics.find((m) => m.sensor_id === selectedDeviceId)

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-4 border-b bg-white flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <h1 className="text-xl font-bold text-gray-900">Live Data</h1>
          <FloorPlanSelector
            floorPlans={floorPlans}
            selectedId={selectedFloorPlanId}
            onChange={setSelectedFloorPlanId}
            isLoading={plansLoading}
          />
          <button
            onClick={() => setShowUploadDialog(true)}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-md"
          >
            + New Floor Plan
          </button>
        </div>

        <div className="flex items-center gap-4">
          {/* Live/Historical Toggle */}
          <div className="flex items-center gap-2 bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setIsLive(true)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                isLive ? 'bg-white shadow text-blue-600' : 'text-gray-600'
              }`}
            >
              Live
            </button>
            <button
              onClick={() => setIsLive(false)}
              className={`px-3 py-1 text-sm rounded-md transition-colors ${
                !isLive ? 'bg-white shadow text-blue-600' : 'text-gray-600'
              }`}
            >
              Historical
            </button>
          </div>

          {/* Heatmap Controls */}
          <label className="flex items-center gap-2 text-sm">
            <input
              type="checkbox"
              checked={showHeatmap}
              onChange={(e) => setShowHeatmap(e.target.checked)}
              className="rounded border-gray-300"
            />
            Show Heatmap
          </label>

          {showHeatmap && (
            <select
              value={heatmapMetric}
              onChange={(e) => setHeatmapMetric(e.target.value as 'count' | 'db')}
              className="px-2 py-1 text-sm border border-gray-300 rounded-md"
            >
              <option value="count">Event Count</option>
              <option value="db">Loudness (dB)</option>
            </select>
          )}
        </div>
      </div>

      {/* Date Range Picker (when historical) */}
      {!isLive && (
        <div className="px-4 py-2 bg-gray-50 border-b">
          <DateRangePicker
            dateRange={dateRange}
            onPresetSelect={setPreset}
            onCustomRangeSelect={setCustomRange}
          />
        </div>
      )}

      {/* Main Content */}
      <div className="flex-1 p-4 bg-gray-100 overflow-hidden">
        {!selectedFloorPlan ? (
          <div className="h-full flex items-center justify-center bg-white rounded-lg border">
            <div className="text-center text-gray-500">
              <p className="mb-4">No floor plan selected</p>
              <button
                onClick={() => setShowUploadDialog(true)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Upload Floor Plan
              </button>
            </div>
          </div>
        ) : (
          <div
            ref={containerRef}
            className="h-full bg-white rounded-lg border overflow-hidden"
          >
            <FloorPlanCanvas
              imageUrl={getFloorPlanImageUrl(selectedFloorPlan.id)}
              width={selectedFloorPlan.width_px}
              height={selectedFloorPlan.height_px}
              devicePositions={positions}
              deviceMetrics={metrics}
              heatmapData={heatmapData}
              showHeatmap={showHeatmap}
              mode={mode}
              onModeChange={setMode}
              onDeviceClick={handleDeviceClick}
              onDeviceDragEnd={handleDeviceDragEnd}
              selectedDeviceId={selectedDeviceId}
              containerWidth={containerSize.width}
              containerHeight={containerSize.height}
            />
          </div>
        )}
      </div>

      {/* Edit Mode Toolbar */}
      {mode === 'edit' && selectedFloorPlanId && (
        <div className="p-3 bg-blue-50 border-t border-blue-200 flex items-center justify-between">
          <span className="text-sm text-blue-800">
            Edit Mode: Drag devices to reposition them
          </span>
          <button
            onClick={() => setShowAddDeviceDialog(true)}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            + Add Device
          </button>
        </div>
      )}

      {/* Modals */}
      {showUploadDialog && (
        <FloorPlanUpload
          onUpload={handleUpload}
          onCancel={() => setShowUploadDialog(false)}
        />
      )}

      {showAddDeviceDialog && selectedFloorPlanId && (
        <DevicePositionForm
          floorPlanId={selectedFloorPlanId}
          availableSensors={availableSensors}
          existingSensorIds={existingSensorIds}
          onSubmit={handleAddDevice}
          onCancel={() => setShowAddDeviceDialog(false)}
        />
      )}

      {selectedDeviceId && (
        <DeviceDetailModal
          sensorId={selectedDeviceId}
          position={selectedPosition}
          metrics={selectedMetrics}
          onClose={() => setSelectedDeviceId(null)}
        />
      )}
    </div>
  )
}
