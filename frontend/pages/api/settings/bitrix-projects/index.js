export default async function handler(req, res) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  const token = req.cookies?.auth_token
  if (!token) return res.status(401).json({ detail: 'Unauthorized' })

  try {
    if (req.method === 'POST') {
      const response = await fetch(`${API_BASE_URL}/api/settings/bitrix-projects`, {
        method: 'POST',
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

    if (req.method === 'GET') {
      const response = await fetch(`${API_BASE_URL}/api/settings/bitrix-projects`, {
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

    return res.status(405).json({ detail: 'Method Not Allowed' })
  } catch (e) {
    return res.status(500).json({ detail: 'Internal error', message: e?.message })
  }
}


