import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // 먼저 백엔드 API 시도
    try {
      const response = await fetch('http://localhost:8000/api/v1/integrated-dashboard/summary', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
        signal: AbortSignal.timeout(2000) // 2초 타임아웃
      })

      if (response.ok) {
        const data = await response.json()
        return NextResponse.json(data)
      }
    } catch (backendError) {
      console.log('Backend API unavailable, falling back to Mock API')
    }

    // 백엔드 실패 시 Mock API로 fallback
    const mockResponse = await fetch('http://localhost:3001/api/dashboard/stats', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!mockResponse.ok) {
      throw new Error(`Mock API error! status: ${mockResponse.status}`)
    }

    const mockData = await mockResponse.json()
    return NextResponse.json(mockData)

  } catch (error) {
    console.error('API 프록시 오류:', error)
    return NextResponse.json(
      {
        success: false,
        error: '백엔드 API 호출에 실패했습니다.',
        details: error instanceof Error ? error.message : '알 수 없는 오류'
      },
      { status: 500 }
    )
  }
}
