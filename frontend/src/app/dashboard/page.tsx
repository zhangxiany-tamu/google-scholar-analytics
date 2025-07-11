'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'

export default function Dashboard() {
  const [scholarId, setScholarId] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const router = useRouter()

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!scholarId.trim()) return
    
    setIsLoading(true)
    setError('')
    
    try {
      // Import the profile first
      const response = await fetch(`http://localhost:8000/api/scholar/import/${encodeURIComponent(scholarId)}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (!response.ok) {
        throw new Error(`Failed to import profile: ${response.statusText}`)
      }
      
      const profileData = await response.json()
      
      // Redirect to analysis results page
      router.push(`/analysis/${profileData.id}`)
      
    } catch (err) {
      console.error('Error analyzing profile:', err)
      setError(err instanceof Error ? err.message : 'Failed to analyze profile')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-white shadow-sm">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Scholar Analytics</h1>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h2 className="text-3xl font-bold text-center text-gray-900 mb-8">
              Analyze Google Scholar Profile
            </h2>
            
            <form onSubmit={handleAnalyze} className="space-y-6">
              <div>
                <input
                  type="text"
                  id="scholar-id"
                  value={scholarId}
                  onChange={(e) => setScholarId(e.target.value)}
                  placeholder="e.g., ABC123XYZ or https://scholar.google.com/citations?hl=en&user=ABC123XYZ"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  disabled={isLoading}
                />
                <p className="mt-2 text-sm text-gray-500">
                  Enter the Google Scholar user ID or paste the full profile URL
                </p>
                {error && (
                  <p className="mt-2 text-sm text-red-600">
                    {error}
                  </p>
                )}
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading || !scholarId.trim()}
                  className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  {isLoading ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Analyzing Profile...
                    </span>
                  ) : (
                    'Analyze Profile'
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
} 