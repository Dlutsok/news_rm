import { Readable } from 'stream'

// Отключаем body parser полностью для поддержки больших файлов
export const config = {
  api: {
    bodyParser: false,
    sizeLimit: '50mb',
    responseLimit: '50mb'
  }
}

export default async function handler(req, res) {
  const API_BASE_URL = process.env.BACKEND_API_URL || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

  console.log('🔶 [Proxy] Входящий запрос:', req.method, req.url)

  // Compose backend endpoint path
  const { path = [] } = req.query
  const endpointPath = '/' + (Array.isArray(path) ? path.join('/') : path)
  console.log('🔶 [Proxy] Endpoint path:', endpointPath)
  

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
  // Skip CSRF for multipart/form-data (file uploads)
  // Enforce only if csrf cookie is present; otherwise allow (e.g., unauthenticated dev calls)
  const unsafeMethods = ['POST', 'PUT', 'PATCH', 'DELETE']
  const contentType = req.headers['content-type'] || ''
  const isMultipart = contentType.includes('multipart/form-data')

  console.log('🔶 [Proxy] CSRF Check:', {
    method: req.method,
    isUnsafe: unsafeMethods.includes(req.method),
    isMultipart,
    hasCsrfCookie: !!csrfCookie,
  })

  if (unsafeMethods.includes(req.method) && !isMultipart) {
    const headerTokenRaw = req.headers['x-csrf-token'] || req.headers['X-CSRF-Token']
    const normalize = (v) => {
      try { return decodeURIComponent(String(v || '')) } catch { return String(v || '') }
    }
    const headerToken = normalize(headerTokenRaw)
    const cookieToken = normalize(csrfCookie)

    console.log('🔶 [Proxy] CSRF Tokens:', {
      headerToken: headerToken ? 'exists' : 'missing',
      cookieToken: cookieToken ? 'exists' : 'missing',
      match: headerToken === cookieToken
    })

    if (csrfCookie && (!headerToken || headerToken !== cookieToken)) {
      console.log('🔴 [Proxy] CSRF token invalid! Blocking request.')
      return res.status(403).json({ error: 'CSRF token invalid' })
    }
  }

  const headers = new Headers()
  if (req.headers['content-type']) headers.set('content-type', req.headers['content-type'])
  if (req.headers['accept']) headers.set('accept', req.headers['accept'])
  if (token) headers.set('authorization', `Bearer ${token}`)

  console.log('🔶 [Proxy] Building request to backend:', url.toString())

  const init = { method: req.method, headers }

  // Для POST/PUT/PATCH/DELETE прокидываем body
  if (req.method !== 'GET' && req.method !== 'HEAD') {
    console.log('🔶 [Proxy] Reading request body...')

    // Для multipart/form-data используем streaming
    if (isMultipart) {
      console.log('🔶 [Proxy] Using stream for multipart')
      init.body = Readable.toWeb(req)
      init.duplex = 'half'
    } else {
      // Для JSON читаем body полностью
      const chunks = []
      for await (const chunk of req) {
        chunks.push(chunk)
      }
      const bodyBuffer = Buffer.concat(chunks)
      console.log('🔶 [Proxy] Body read:', bodyBuffer.length, 'bytes')

      if (bodyBuffer.length > 0) {
        init.body = bodyBuffer.toString('utf-8')
      }
    }
  }

  // Определяем таймаут для разных эндпоинтов
  let timeoutMs = 60000 // 1 минута по умолчанию
  if (apiPath.includes('/url-articles/') || apiPath.includes('/news-generation/') || apiPath.includes('/news/parse')) {
    timeoutMs = 120000 // 2 минуты для долгих операций
    console.log('🔶 [Proxy] Long operation detected, timeout:', timeoutMs / 1000, 'sec')
  }

  const controller = new AbortController()
  const timeoutId = setTimeout(() => {
    console.log('🔴 [Proxy] TIMEOUT after', timeoutMs / 1000, 'seconds!')
    controller.abort()
  }, timeoutMs)

  console.log('🔶 [Proxy] Sending fetch to backend...')
  try {
    const response = await fetch(url.toString(), { ...init, signal: controller.signal })
    clearTimeout(timeoutId)
    console.log('🔶 [Proxy] Got response from backend:', response.status)
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
    clearTimeout(timeoutId)
    if (e.name === 'AbortError') {
      console.error('🔴 [Proxy] Request timeout after', timeoutMs / 1000, 'seconds')
      return res.status(408).json({ error: 'Request timeout', detail: `Request timeout after ${timeoutMs / 1000} seconds` })
    }
    console.error('🔴 [Proxy] Error:', e)
    return res.status(502).json({ error: 'Proxy error', detail: e?.message })
  }
}


