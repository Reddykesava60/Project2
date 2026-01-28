import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')

        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const { searchParams } = new URL(request.url)
        const restaurant = searchParams.get('restaurant')

        const url = restaurant
            ? `${BACKEND_URL}/api/v1/orders/dashboard/stats/?restaurant=${restaurant}`
            : `${BACKEND_URL}/api/v1/orders/dashboard/stats/`

        const response = await fetch(url, {
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        })

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            return NextResponse.json(error, { status: response.status })
        }

        const data = await response.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error('Dashboard stats API error:', error)
        return NextResponse.json({ error: 'Server error' }, { status: 500 })
    }
}
