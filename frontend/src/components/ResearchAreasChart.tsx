'use client'

import { useEffect, useRef } from 'react'

interface ResearchAreasChartProps {
  data: { [key: string]: number }
}

export default function ResearchAreasChart({ data }: ResearchAreasChartProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    if (!canvasRef.current || !data || Object.keys(data).length === 0) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Set canvas size
    const size = 250
    canvas.width = size
    canvas.height = size

    // Clear canvas
    ctx.clearRect(0, 0, size, size)

    // Prepare data
    const entries = Object.entries(data).slice(0, 6) // Top 6 areas
    const total = entries.reduce((sum, [, value]) => sum + value, 0)
    
    if (total === 0) return

    // Colors for each slice - multiple colors for research areas
    const colors = [
      '#3B82F6', // blue
      '#10B981', // green
      '#8B5CF6', // purple
      '#F59E0B', // amber
      '#EF4444', // red
      '#6B7280', // gray
    ]

    // Draw pie chart
    const centerX = size / 2
    const centerY = size / 2
    const radius = Math.min(size / 2 - 15, 100)

    let currentAngle = -Math.PI / 2 // Start at top

    entries.forEach(([area, value], index) => {
      const sliceAngle = (value / total) * 2 * Math.PI
      
      // Draw slice
      ctx.beginPath()
      ctx.moveTo(centerX, centerY)
      ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle)
      ctx.closePath()
      ctx.fillStyle = colors[index]
      ctx.fill()
      
      // Draw slice border
      ctx.strokeStyle = '#ffffff'
      ctx.lineWidth = 2
      ctx.stroke()

      currentAngle += sliceAngle
    })

    // Draw center circle for donut effect
    ctx.beginPath()
    ctx.arc(centerX, centerY, radius * 0.4, 0, 2 * Math.PI)
    ctx.fillStyle = '#ffffff'
    ctx.fill()
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 2
    ctx.stroke()

  }, [data])

  if (!data || Object.keys(data).length === 0) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-500">
        No research area data available
      </div>
    )
  }

  const entries = Object.entries(data).slice(0, 6)
  const colors = [
    '#3B82F6', '#10B981', '#8B5CF6', '#F59E0B', '#EF4444', '#6B7280'
  ]

  return (
    <div className="flex flex-col lg:flex-row items-center gap-6">
      {/* Chart */}
      <div className="flex-shrink-0">
        <canvas 
          ref={canvasRef}
          className="max-w-full h-auto"
        />
      </div>

      {/* Legend */}
      <div className="flex-1">
        <div className="space-y-3">
          {entries.map(([area, percentage], index) => (
            <div key={area} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <div 
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: colors[index] }}
                ></div>
                <span className="text-sm font-medium capitalize">
                  {area.replace('_', ' ')}
                </span>
              </div>
              <span className="text-sm text-gray-600 font-semibold">
                {percentage.toFixed(1)}%
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}