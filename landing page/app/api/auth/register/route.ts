import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/mongodb'
import { hashPassword, setAuthCookie } from '@/lib/auth'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { username, email, password } = body

    if (!username?.trim() || !email?.trim() || !password)
      return NextResponse.json({ error: 'All fields are required.' }, { status: 400 })

    if (password.length < 6)
      return NextResponse.json({ error: 'Password must be at least 6 characters.' }, { status: 400 })

    let db
    try {
      db = await getDb()
    } catch (dbErr: any) {
      console.error('[register] DB connect failed:', dbErr?.message)
      return NextResponse.json(
        { error: 'Cannot connect to database. Check MongoDB Atlas — IP whitelist and cluster status.' },
        { status: 503 }
      )
    }

    const users = db.collection('users')

    const existing = await users.findOne({
      $or: [
        { email: email.toLowerCase().trim() },
        { username: username.toLowerCase().trim() },
      ],
    })
    if (existing) {
      const field = existing.email === email.toLowerCase().trim() ? 'Email' : 'Username'
      return NextResponse.json({ error: `${field} is already taken.` }, { status: 409 })
    }

    const hashed = await hashPassword(password)
    const result = await users.insertOne({
      username:    username.trim(),
      email:       email.toLowerCase().trim(),
      password:    hashed,
      createdAt:   new Date(),
      preferences: { provider: 'groq', memories: [] },
    })

    await setAuthCookie({
      userId:   result.insertedId.toString(),
      email:    email.toLowerCase().trim(),
      username: username.trim(),
    })

    return NextResponse.json({ ok: true, username: username.trim() })

  } catch (err: any) {
    console.error('[register] Unexpected error:', err?.message, err?.stack)
    return NextResponse.json(
      { error: `Server error: ${err?.message ?? 'Unknown error'}` },
      { status: 500 }
    )
  }
}
