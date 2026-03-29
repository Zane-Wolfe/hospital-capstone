import { Circle, Text, Group } from 'react-konva'
import type { KonvaEventObject } from 'konva/lib/Node'

interface DeviceMarkerProps {
  sensorId: string
  x: number
  y: number
  label?: string | null
  isOnline?: boolean
  isSelected?: boolean
  draggable?: boolean
  onDragEnd?: (sensorId: string, x: number, y: number) => void
  onClick?: (sensorId: string) => void
  onMouseEnter?: (sensorId: string, e: KonvaEventObject<MouseEvent>) => void
  onMouseLeave?: () => void
}

export function DeviceMarker({
  sensorId,
  x,
  y,
  label,
  isOnline = true,
  isSelected = false,
  draggable = false,
  onDragEnd,
  onClick,
  onMouseEnter,
  onMouseLeave,
}: DeviceMarkerProps) {
  const radius = 12
  const fillColor = isOnline ? '#22c55e' : '#ef4444'
  const strokeColor = isSelected ? '#3b82f6' : '#ffffff'
  const strokeWidth = isSelected ? 3 : 2

  const handleDragEnd = (e: KonvaEventObject<DragEvent>) => {
    if (onDragEnd) {
      onDragEnd(sensorId, e.target.x(), e.target.y())
    }
  }

  const handleClick = () => {
    if (onClick) {
      onClick(sensorId)
    }
  }

  const handleMouseEnter = (e: KonvaEventObject<MouseEvent>) => {
    if (onMouseEnter) {
      onMouseEnter(sensorId, e)
    }
    const container = e.target.getStage()?.container()
    if (container) {
      container.style.cursor = draggable ? 'grab' : 'pointer'
    }
  }

  const handleMouseLeave = (e: KonvaEventObject<MouseEvent>) => {
    if (onMouseLeave) {
      onMouseLeave()
    }
    const container = e.target.getStage()?.container()
    if (container) {
      container.style.cursor = 'default'
    }
  }

  return (
    <Group
      x={x}
      y={y}
      draggable={draggable}
      onDragEnd={handleDragEnd}
      onClick={handleClick}
      onTap={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      <Circle
        radius={radius}
        fill={fillColor}
        stroke={strokeColor}
        strokeWidth={strokeWidth}
        shadowColor="black"
        shadowBlur={4}
        shadowOpacity={0.3}
      />
      {label && (
        <Text
          text={label}
          fontSize={10}
          fill="#ffffff"
          fontStyle="bold"
          align="center"
          verticalAlign="middle"
          offsetX={label.length * 2.5}
          offsetY={5}
        />
      )}
      <Text
        text={sensorId.slice(-4)}
        fontSize={8}
        fill="#ffffff"
        y={radius + 4}
        align="center"
        offsetX={12}
      />
    </Group>
  )
}
