export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method Not Allowed' })
  }

  const isProd = process.env.NODE_ENV === 'production'
  const cookieBase = [
    'Path=/',
    'SameSite=Lax',
    isProd ? 'Secure' : '',
  ].filter(Boolean).join('; ')

  res.setHeader('Set-Cookie', [
    `auth_token=; HttpOnly; Max-Age=0; ${cookieBase}`,
    `csrf_token=; Max-Age=0; ${cookieBase}`,
  ])

  return res.status(200).json({ success: true })
}


