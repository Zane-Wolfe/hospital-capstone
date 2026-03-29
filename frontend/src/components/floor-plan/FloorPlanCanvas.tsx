import { useState, useRef, useCallback, useEffect } from 'react'
import { Stage, Layer } from 'react-konva'
import type { KonvaEventObject } from 'konva/lib/Node'
import type Konva from 'konva'
import { FloorPlanImage } from './FloorPlanImage'
import { DeviceMarker } from './DeviceMarker'
import { HeatmapOverlay } from './HeatmapOverlay'
import { FloorPlanControls } from './FloorPlanControls'
import type { DevicePosition, PositionalHeatmapPoint, DeviceMetrics } from '../../types'

interface FloorPlanCanvasProps {
  imageUrl: string
  width: number
  height: number
  devicePositions: DevicePosition[]
  deviceMetrics?: DeviceMetrics[]
  heatmapData?: PositionalHeatmapPoint[]
  showHeatmap?: boolean
  mode?: 'view' | 'edit'
  onModeChange?: (mode: 'view' | 'edit') => void
  onDeviceClick?: (sensorId: string) => void
  onDeviceDragEnd?: (sensorId: string, x: number, y: number) => void
  selectedDeviceId?: string | null
  containerWidth?: number
  containerHeight?: number
}

const MIN_SCALE = 0.5
const MAX_SCALE = 3
const SCALE_STEP = 0.1

export function FloorPlanCanvas({
  imageUrl,
  width,
  height,
  devicePositions,
  deviceMetrics = [],
  heatmapData = [],
  showHeatmap = false,
  mode = 'view',
  onModeChange,
  onDeviceClick,
  onDeviceDragEnd,
  selectedDeviceId,
  containerWidth,
  containerHeight,
}: FloorPlanCanvasProps) {
  const stageRef = useRef<Konva.Stage>(null)
  const [scale, setScaleInternal] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [internalMode, setInternalMode] = useState<'view' | 'edit'>(mode)
  const scaleRef = useRef(1)

  // Wrapper to keep ref in sync with state synchronously
  const setScale = useCallback((newScale: number) => {
    scaleRef.current = newScale
    setScaleInternal(newScale)
  }, [])

  // Compute initial scale to fit container
  useEffect(() => {
    if (containerWidth && containerHeight) {
      const scaleX = containerWidth / width
      const scaleY = containerHeight / height
      const newScale = Math.min(scaleX, scaleY, 1)
      setScale(newScale)
      // Center the image (constrained)
      const centeredX = (containerWidth - width * newScale) / 2
      const centeredY = (containerHeight - height * newScale) / 2

      // Apply constraints
      const scaledWidth = width * newScale
      const scaledHeight = height * newScale
      const minX = Math.min(0, containerWidth - scaledWidth)
      const maxX = Math.max(0, containerWidth - scaledWidth)
      const minY = Math.min(0, containerHeight - scaledHeight)
      const maxY = Math.max(0, containerHeight - scaledHeight)

      setPosition({
        x: Math.min(Math.max(centeredX, minX), maxX),
        y: Math.min(Math.max(centeredY, minY), maxY),
      })
    }
  }, [containerWidth, containerHeight, width, height, setScale])

  const actualMode = onModeChange ? mode : internalMode

  // Constrain position so image can't be dragged off screen
  const constrainPosition = useCallback(
    (x: number, y: number, currentScale: number) => {
      const scaledWidth = width * currentScale
      const scaledHeight = height * currentScale
      const viewWidth = containerWidth || width
      const viewHeight = containerHeight || height

      let constrainedX: number
      let constrainedY: number

      if (scaledWidth <= viewWidth) {
        // Image fits in viewport horizontally - keep entire image visible
        // x >= 0 (left edge at or after viewport left)
        // x <= viewWidth - scaledWidth (right edge at or before viewport right)
        constrainedX = Math.max(0, Math.min(x, viewWidth - scaledWidth))
      } else {
        // Image wider than viewport - can pan to see all parts
        // x <= 0 (left edge at or before viewport left, to see left side)
        // x >= viewWidth - scaledWidth (right edge at or after viewport right, to see right side)
        constrainedX = Math.min(0, Math.max(x, viewWidth - scaledWidth))
      }

      if (scaledHeight <= viewHeight) {
        // Image fits in viewport vertically - keep entire image visible
        constrainedY = Math.max(0, Math.min(y, viewHeight - scaledHeight))
      } else {
        // Image taller than viewport - can pan to see all parts
        constrainedY = Math.min(0, Math.max(y, viewHeight - scaledHeight))
      }

      return { x: constrainedX, y: constrainedY }
    },
    [width, height, containerWidth, containerHeight]
  )

  const handleModeChange = (newMode: 'view' | 'edit') => {
    if (onModeChange) {
      onModeChange(newMode)
    } else {
      setInternalMode(newMode)
    }
  }

  const handleWheel = useCallback((e: KonvaEventObject<WheelEvent>) => {
    e.evt.preventDefault()
    const stage = stageRef.current
    if (!stage) return

    const oldScale = scale
    const pointer = stage.getPointerPosition()
    if (!pointer) return

    const mousePointTo = {
      x: (pointer.x - position.x) / oldScale,
      y: (pointer.y - position.y) / oldScale,
    }

    const direction = e.evt.deltaY > 0 ? -1 : 1
    const newScale = Math.min(
      MAX_SCALE,
      Math.max(MIN_SCALE, oldScale + direction * SCALE_STEP)
    )

    const newX = pointer.x - mousePointTo.x * newScale
    const newY = pointer.y - mousePointTo.y * newScale
    const constrained = constrainPosition(newX, newY, newScale)

    setScale(newScale)
    setPosition(constrained)
  }, [scale, position, constrainPosition, setScale])

  const handleZoomIn = useCallback(() => {
    const newScale = Math.min(MAX_SCALE, scale + SCALE_STEP)
    const constrained = constrainPosition(position.x, position.y, newScale)
    setScale(newScale)
    setPosition(constrained)
  }, [scale, position, constrainPosition, setScale])

  const handleZoomOut = useCallback(() => {
    const newScale = Math.max(MIN_SCALE, scale - SCALE_STEP)
    const constrained = constrainPosition(position.x, position.y, newScale)
    setScale(newScale)
    setPosition(constrained)
  }, [scale, position, constrainPosition, setScale])

  const handleReset = useCallback(() => {
    if (containerWidth && containerHeight) {
      const scaleX = containerWidth / width
      const scaleY = containerHeight / height
      const newScale = Math.min(scaleX, scaleY, 1)
      const centeredX = (containerWidth - width * newScale) / 2
      const centeredY = (containerHeight - height * newScale) / 2
      const constrained = constrainPosition(centeredX, centeredY, newScale)
      setScale(newScale)
      setPosition(constrained)
    } else {
      setScale(1)
      setPosition({ x: 0, y: 0 })
    }
  }, [containerWidth, containerHeight, width, height, constrainPosition, setScale])

  const handleDragMove = useCallback((e: KonvaEventObject<DragEvent>) => {
    const stage = e.target as Konva.Stage
    const currentX = stage.x()
    const currentY = stage.y()
    const constrained = constrainPosition(currentX, currentY, scaleRef.current)

    // Only update if position changed (to avoid unnecessary re-renders)
    if (constrained.x !== currentX || constrained.y !== currentY) {
      stage.x(constrained.x)
      stage.y(constrained.y)
    }
  }, [constrainPosition])

  const handleDragEnd = useCallback((e: KonvaEventObject<DragEvent>) => {
    const constrained = constrainPosition(e.target.x(), e.target.y(), scaleRef.current)
    setPosition(constrained)
  }, [constrainPosition])

  const getDeviceOnlineStatus = (sensorId: string): boolean => {
    const metrics = deviceMetrics.find((m) => m.sensor_id === sensorId)
    return metrics?.is_online ?? false
  }

  const stageWidth = containerWidth || width
  const stageHeight = containerHeight || height

  return (
    <div className="relative">
      <Stage
        ref={stageRef}
        width={stageWidth}
        height={stageHeight}
        scaleX={scale}
        scaleY={scale}
        x={position.x}
        y={position.y}
        draggable={actualMode === 'view'}
        onDragMove={handleDragMove}
        onDragEnd={handleDragEnd}
        onWheel={handleWheel}
      >
        <Layer>
          <FloorPlanImage imageUrl={imageUrl} width={width} height={height} />
        </Layer>

        {showHeatmap && heatmapData.length > 0 && (
          <Layer>
            <HeatmapOverlay data={heatmapData} width={width} height={height} />
          </Layer>
        )}

        <Layer>
          {devicePositions.map((device) => (
            <DeviceMarker
              key={device.sensor_id}
              sensorId={device.sensor_id}
              x={device.x_coord}
              y={device.y_coord}
              label={device.label}
              isOnline={getDeviceOnlineStatus(device.sensor_id)}
              isSelected={selectedDeviceId === device.sensor_id}
              draggable={actualMode === 'edit'}
              onClick={onDeviceClick}
              onDragEnd={onDeviceDragEnd}
            />
          ))}
        </Layer>
      </Stage>

      <FloorPlanControls
        scale={scale}
        onZoomIn={handleZoomIn}
        onZoomOut={handleZoomOut}
        onReset={handleReset}
        mode={actualMode}
        onModeChange={handleModeChange}
      />
    </div>
  )
}
