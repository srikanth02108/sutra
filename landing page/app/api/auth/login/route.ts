import { NextRequest, NextResponse } from 'next/server'
import { getDb } from '@/lib/mongodb'
import { verifyPassword, hashPassword, setAuthCookie } from '@/lib/auth'

const DEMO_EMAIL    = process.env.DEMO_EMAIL    ?? 'demo@officenator.ai'
const DEMO_PASSWORD = process.env.DEMO_PASSWORD ?? 'demo1234'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { email, password, demo } = body

    // ── Connect to DB ─────────────────────────────────────────────────
    let db
    try {
      db = await getDb()
    } catch (dbErr: any) {
      console.error('[login] DB connect failed:', dbErr?.message)
      return NextResponse.json(
        { error: 'Cannot connect to database. Check MongoDB Atlas — IP whitelist and cluster status.' },
        { status: 503 }
      )
    }

    const users = db.collection('users')

    // ── Demo login ─────────────────────────────────────────────────────
    if (demo === true) {
      let demoUser = await users.findOne({ email: DEMO_EMAIL })

      if (!demoUser) {
        const hashed = await hashPassword(DEMO_PASSWORD)
        const result = await users.insertOne({
          username:    'demo',
          email:       DEMO_EMAIL,
          password:    hashed,
          isDemo:      true,
          createdAt:   new Date(),
          preferences: { provider: 'groq', memories: [] },
        })
        demoUser = { _id: result.insertedId, username: 'demo', email: DEMO_EMAIL }
      }

      await setAuthCookie({
        userId:   demoUser._id.toString(),
        email:    DEMO_EMAIL,
        username: 'demo',
      })

      return NextResponse.json({ ok: true, username: 'demo', isDemo: true })
    }

    // ── Normal login ───────────────────────────────────────────────────
    if (!email?.trim() || !password)
      return NextResponse.json({ error: 'Email and password are required.' }, { status: 400 })

    const user = await users.findOne({ email: email.toLowerCase().trim() })
    if (!user)
      return NextResponse.json({ error: 'No account found with that email.' }, { status: 401 })

    const valid = await verifyPassword(password, user.password)
    if (!valid)
      return NextResponse.json({ error: 'Incorrect password.' }, { status: 401 })

    await setAuthCookie({
      userId:   user._id.toString(),
      email:    user.email,
      username: user.username,
    })

    return NextResponse.json({ ok: true, username: user.username })

  } catch (err: any) {
    console.error('[login] Unexpected error:', err?.message, err?.stack)
    return NextResponse.json(
      { error: `Server error: ${err?.message ?? 'Unknown error'}` },
      { status: 500 }
    )
  }
}
