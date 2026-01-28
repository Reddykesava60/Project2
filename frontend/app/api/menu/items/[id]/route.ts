import { NextRequest, NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

interface RouteParams {
    params: { id: string }
}

export async function PATCH(request: NextRequest, { params }: RouteParams) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')

        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const body = await request.json()

        const response = await fetch(`${BACKEND_URL}/api/v1/menu/items/${params.id}/`, {
            method: 'PATCH',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(body),
        })

        if (!response.ok) {
            const error = await response.json().catch(() => ({}))
            return NextResponse.json(error, { status: response.status })
        }

        const data = await response.json()
        return NextResponse.json(data)
    } catch (error) {
        console.error('Item PATCH error:', error)
        return NextResponse.json({ error: 'Server error' }, { status: 500 })
    }
}

export async function DELETE(request: NextRequest, { params }: RouteParams) {
    try {
        const token = request.headers.get('authorization')?.replace('Bearer ', '')

        if (!token) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }

        const response = await fetch(`${BACKEND_URL}/api/v1/menu/items/${params.id}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${token}`,
            },
        })

        if (!response.ok && response.status !== 204) {
            const error = await response.json().catch(() => ({}))
            return NextResponse.json(error, { status: response.status })
        }

        return NextResponse.json({ success: true })
    } catch (error) {
        console.error('Item DELETE error:', error)
        return NextResponse.json({ error: 'Server error' }, { status: 500 })
    }
}
