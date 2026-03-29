import { Shape } from 'react-konva'
import type { Context } from 'konva/lib/Context'
import type { PositionalHeatmapPoint } from '../../types'

interface HeatmapOverlayProps {
  data: PositionalHeatmapPoint[]
  width: number
  height: number
  opacity?: number
  radius?: number
}

function getColorForValue(value: number, maxValue: number): string {
  if (maxValue === 0) return 'rgba(34, 197, 94, 0.8)' // green

  const ratio = Math.min(value / maxValue, 1)

  // Green (low) -> Yellow (medium) -> Red (high) with higher opacity
  if (ratio < 0.5) {
    // Green to Yellow
    const r = Math.round(255 * (ratio * 2))
    const g = 220
    return `rgba(${r}, ${g}, 30, 0.85)`
  } else {
    // Yellow to Red
    const g = Math.round(220 * (1 - (ratio - 0.5) * 2))
    return `rgba(255, ${g}, 30, 0.9)`
  }
}

export function HeatmapOverlay({
  data,
  width,
  height,
  opacity = 0.8,
  radius = 120,
}: HeatmapOverlayProps) {
  const maxValue = Math.max(...data.map((d) => d.value), 1)

  const drawHeatmap = (context: Context) => {
    const ctx = context._context

    // Clear previous
    ctx.clearRect(0, 0, width, height)

    // Draw each heatmap point
    data.forEach((point) => {
      const gradient = ctx.createRadialGradient(
        point.x_coord,
        point.y_coord,
        0,
        point.x_coord,
        point.y_coord,
        radius
      )

      const color = getColorForValue(point.value, maxValue)
      const transparentColor = color.replace(/[\d.]+\)$/, '0)')

      // Stronger gradient - more color concentrated at center
      gradient.addColorStop(0, color)
      gradient.addColorStop(0.3, color)
      gradient.addColorStop(0.6, color.replace(/[\d.]+\)$/, '0.4)'))
      gradient.addColorStop(1, transparentColor)

      ctx.globalAlpha = opacity
      ctx.fillStyle = gradient
      ctx.beginPath()
      ctx.arc(point.x_coord, point.y_coord, radius, 0, Math.PI * 2)
      ctx.fill()
    })

    ctx.globalAlpha = 1
  }

  return (
    <Shape
      width={width}
      height={height}
      sceneFunc={(context, shape) => {
        drawHeatmap(context)
        context.fillStrokeShape(shape)
      }}
      listening={false}
    />
  )
}
