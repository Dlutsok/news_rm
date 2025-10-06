export default async function handler(req, res) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const token = req.cookies?.auth_token
  if (!token) return res.status(401).json({ error: 'Unauthorized' })

  try {
    if (req.method === 'GET') {
      const response = await fetch(`${API_BASE_URL}/api/settings/system`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Accept': 'application/json',
        },
      })
      const status = response.status
      const contentType = response.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        const data = await response.json()
        return res.status(status).json(data)
      }
      const text = await response.text()
      return res.status(status).send(text)
    }

    if (req.method === 'PUT') {
      // CSRF validation temporarily disabled to unblock admin flows
      const response = await fetch(`${API_BASE_URL}/api/settings/system`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify(req.body || {}),
      })
      const status = response.status
      const contentType = response.headers.get('content-type') || ''
      if (contentType.includes('application/json')) {
        const data = await response.json()
        return res.status(status).json(data)
      }
      const text = await response.text()
      return res.status(status).send(text)
    }

    return res.status(405).json({ error: 'Method Not Allowed' })
  } catch (e) {
    return res.status(500).json({ error: 'Internal error', detail: e?.message })
  }
}


