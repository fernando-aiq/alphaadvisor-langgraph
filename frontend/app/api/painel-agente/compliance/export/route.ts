import { NextRequest, NextResponse } from 'next/server'

export const dynamic = 'force-dynamic'

function getBackendUrl() {
  const url = process.env.API_URL || 
              process.env.NEXT_PUBLIC_API_URL || 
              'http://localhost:8000'
  return url
}

const BACKEND_URL = getBackendUrl()

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const backendUrl = `${BACKEND_URL}/api/painel-agente/compliance/export?${searchParams.toString()}`
    
    const response = await fetch(backendUrl, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => 'Unknown error')
      return NextResponse.json(
        { error: 'Backend request failed', details: errorText },
        { status: response.status }
      )
    }

    // Se for CSV, retornar como blob
    const contentType = response.headers.get('content-type')
    if (contentType?.includes('text/csv')) {
      const blob = await response.blob()
      return new NextResponse(blob, {
        headers: {
          'Content-Type': 'text/csv',
          'Content-Disposition': `attachment; filename=compliance_export_${new Date().toISOString().split('T')[0]}.csv`
        }
      })
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error: any) {
    console.error('[API Route /api/painel-agente/compliance/export] Erro:', error)
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

