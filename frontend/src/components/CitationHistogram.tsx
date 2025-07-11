'use client'

import { useMemo } from 'react'

interface CitationHistogramProps {
  papers: any[]
}

export default function CitationHistogram({ papers }: CitationHistogramProps) {
  const chartData = useMemo(() => {
    if (!papers || papers.length === 0) return null

    const currentYear = new Date().getFullYear()
    const years = papers
      .map(p => p.year)
      .filter(y => y && y >= 1990 && y <= currentYear)
    
    if (years.length === 0) return null

    const minYear = Math.min(...years)
    const maxYear = Math.max(...years)

    // Create year buckets
    const yearCounts: { [key: number]: number } = {}
    for (let year = minYear; year <= maxYear; year++) {
      yearCounts[year] = 0
    }

    // Count papers per year
    years.forEach(year => {
      yearCounts[year] = (yearCounts[year] || 0) + 1
    })

    const maxCount = Math.max(...Object.values(yearCounts))
    const yearArray = Object.keys(yearCounts).map(Number).sort((a, b) => a - b)

    return {
      yearCounts,
      yearArray,
      maxCount,
      minYear,
      maxYear
    }
  }, [papers])

  if (!chartData) {
    return (
      <div className="mt-4">
        <h5 className="text-sm font-medium text-gray-700 mb-2">Publications over time</h5>
        <div className="flex items-center justify-center h-16 text-gray-500 text-sm bg-gray-50 rounded">
          No data available
        </div>
      </div>
    )
  }

  const { yearCounts, yearArray, maxCount } = chartData

  return (
    <div className="mt-4">
      <h5 className="text-sm font-medium text-gray-700 mb-2">Publications over time</h5>
      <div className="bg-white border border-gray-200 rounded p-3">
        {/* Chart area */}
        <div className="flex items-end justify-between h-20 mb-2 space-x-0.5">
          {yearArray.map((year) => {
            const count = yearCounts[year]
            const height = maxCount > 0 ? Math.max(2, (count / maxCount) * 80) : 0
            
            return (
              <div key={year} className="flex-1 flex flex-col items-center group">
                <div 
                  className="w-full bg-blue-500 hover:bg-blue-600 transition-colors rounded-sm cursor-pointer relative"
                  style={{ height: `${height}px` }}
                  title={`${year}: ${count} publication${count !== 1 ? 's' : ''}`}
                >
                  {count > 0 && (
                    <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-1 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                      {count}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
        
        {/* Year labels */}
        <div className="flex justify-between text-xs text-gray-500">
          <span>{yearArray[0]}</span>
          {yearArray.length > 4 && (
            <span>{yearArray[Math.floor(yearArray.length / 2)]}</span>
          )}
          <span>{yearArray[yearArray.length - 1]}</span>
        </div>
        
        {/* Summary stats */}
        <div className="mt-2 pt-2 border-t border-gray-100 text-xs text-gray-600">
          <div className="flex justify-between">
            <span>Total: {papers.length} papers</span>
            <span>Peak: {maxCount} in a year</span>
          </div>
        </div>
      </div>
    </div>
  )
}