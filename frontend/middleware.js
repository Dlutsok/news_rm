import { NextResponse } from 'next/server'

export function middleware(req) {
  const url = req.nextUrl
  const token = req.cookies.get('auth_token')?.value

  // Public paths that don't require auth
  const publicPaths = ['/login', '/test-icons', '/api']
  const isPublic = publicPaths.some((p) => url.pathname === p || url.pathname.startsWith(p))

  // If not public and no token, redirect to login
  if (!isPublic && !token) {
    // Избегаем петли, если уже на /login
    if (url.pathname !== '/login') {
      const loginUrl = new URL('/login', url.origin)
      loginUrl.searchParams.set('next', url.pathname)
      return NextResponse.redirect(loginUrl)
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon|robots|sitemap).*)'],
}


