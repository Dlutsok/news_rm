export default async function handler(req, res) {
  const API_BASE_URL = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
  
  console.log('Proxy API_BASE_URL:', API_BASE_URL)

  // Compose backend endpoint path
  const { path = [] } = req.query
  const endpointPath = '/' + (Array.isArray(path) ? path.join('/') : path)
  

  // Allow proxying backend auth endpoints; only avoid proxying to our own proxy
  if (endpointPath.startsWith('/api/proxy')) {
    return res.status(400).json({ error: 'Invalid proxy target' })
  }

  // Build target URL
  const apiPath = endpointPath.startsWith('/api') ? endpointPath : '/api' + endpointPath
  const url = new URL(API_BASE_URL + apiPath)
  // Preserve query string
  Object.entries(req.query).forEach(([key, value]) => {
    if (key !== 'path') {
      if (Array.isArray(value)) value.forEach((v) => url.searchParams.append(key, v))
      else url.searchParams.set(key, value)
    }
  })

  const token = req.cookies?.auth_token
  const csrfCookie = req.cookies?.csrf_token

  // CSRF check for non-idempotent methods
  // Enforce only if csrf cookie is present; otherwise allow (e.g., unauthenticated dev calls)
  const unsafeMethods = ['POST', 'PUT', 'PATCH', 'DELETE']
  if (unsafeMethods.includes(req.method)) {
    const headerTokenRaw = req.headers['x-csrf-token'] || req.headers['X-CSRF-Token']
    const normalize = (v) => {
      try { return decodeURIComponent(String(v || '')) } catch { return String(v || '') }
    }
    const headerToken = normalize(headerTokenRaw)
    const cookieToken = normalize(csrfCookie)
    if (csrfCookie && (!headerToken || headerToken !== cookieToken)) {
      return res.status(403).json({ error: 'CSRF token invalid' })
    }
  }

  const headers = new Headers()
  if (req.headers['content-type']) headers.set('content-type', req.headers['content-type'])
  if (req.headers['accept']) headers.set('accept', req.headers['accept'])
  if (token) headers.set('authorization', `Bearer ${token}`)

  const init = { method: req.method, headers }
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    const body = typeof req.body === 'string' ? req.body : JSON.stringify(req.body || {})
    init.body = body
  }

  try {
    const response = await fetch(url.toString(), init)
    const contentType = response.headers.get('content-type') || ''
    const status = response.status

    if (contentType.includes('application/json')) {
      const data = await response.json()
      return res.status(status).json(data)
    }

    const buf = await response.arrayBuffer()
    res.status(status)
    response.headers.forEach((v, k) => {
      if (k.toLowerCase() === 'content-encoding') return
      res.setHeader(k, v)
    })
    return res.send(Buffer.from(buf))
  } catch (e) {
    return res.status(502).json({ error: 'Proxy error', detail: e?.message })
  }
}


