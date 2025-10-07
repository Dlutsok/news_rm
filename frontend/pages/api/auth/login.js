export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' })
  }

  try {
    const API_BASE_URL = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    console.log('[Login API] Using API_BASE_URL:', API_BASE_URL)
    
    const { username, password } = req.body || {}

    if (!username || !password) {
      console.error('[Login API] Missing credentials')
      return res.status(400).json({ error: 'Missing credentials' })
    }

    console.log('[Login API] Attempting login for user:', username)
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    
    console.log('[Login API] Backend response status:', response.status)

    const data = await response.json()
    if (!response.ok) {
      return res.status(response.status).json({ error: data.detail || 'Login failed' })
    }

    const token = data.access_token
    if (!token) {
      return res.status(500).json({ error: 'Token not received from backend' })
    }

    // Generate CSRF token
    const csrfToken = Math.random().toString(36).slice(2) + Math.random().toString(36).slice(2)

    const isProd = process.env.NODE_ENV === 'production'
    const cookieBase = [
      'Path=/',
      'SameSite=Lax',
      isProd ? 'Secure' : '',
    ].filter(Boolean).join('; ')

    // Set HttpOnly auth cookie
    res.setHeader('Set-Cookie', [
      `auth_token=${encodeURIComponent(token)}; HttpOnly; Max-Age=${60 * 60 * 24 * 7}; ${cookieBase}`,
      `csrf_token=${encodeURIComponent(csrfToken)}; Max-Age=${60 * 60 * 24 * 7}; ${cookieBase}`,
    ])

    return res.status(200).json({ success: true })
  } catch (err) {
    return res.status(500).json({ error: 'Internal error' })
  }
}


