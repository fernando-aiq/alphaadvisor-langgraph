import { NextRequest, NextResponse } from 'next/server'

function getBackendUrl() {
  const url = process.env.API_URL || 
              process.env.NEXT_PUBLIC_API_URL || 
              'http://localhost:8000'
  return url
}

const BACKEND_URL = getBackendUrl()

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ traceId: string }> }
) {
  try {
    console.log('[API Route /api/trace/[traceId]/tools] Route called')
    const { traceId } = await params
    console.log('[API Route /api/trace/[traceId]/tools] TraceId:', traceId)
    console.log('[API Route /api/trace/[traceId]/tools] Backend URL:', BACKEND_URL)
    
    const backendUrl = `${BACKEND_URL}/api/trace/${traceId}/tools`
    console.log('[API Route /api/trace/[traceId]/tools] Calling backend:', backendUrl)
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    console.log('[API Route /api/trace/[traceId]/tools] Backend response status:', response.status)

    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      return NextResponse.json(
        { error: 'Backend request failed', details: errorText },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[API Route /api/trace/[traceId]/tools] Erro:', error)
    console.error('[API Route /api/trace/[traceId]/tools] Stack:', error.stack)
    return NextResponse.json(
      { 
        error: error.message || 'Internal server error', 
        type: error.name,
        details: process.env.NODE_ENV === 'development' ? error.stack : undefined
      },
      { status: 500 }
    )
  }
}

