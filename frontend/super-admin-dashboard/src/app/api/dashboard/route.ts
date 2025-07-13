import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // 백엔드 API 호출
    const response = await fetch('http://localhost:8000/api/v1/integrated-dashboard/summary', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const data = await response.json()
    
    return NextResponse.json(data)
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
