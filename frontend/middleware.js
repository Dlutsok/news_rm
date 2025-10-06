import { NextResponse } from 'next/server'

export function middleware(req) {
  const url = req.nextUrl
  const token = req.cookies.get('auth_token')?.value

  // Paths that require auth
  const protectedPaths = ['/', '/settings']
  const isProtected = protectedPaths.some((p) => url.pathname === p)

  if (isProtected && !token) {
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
  matcher: ['/', '/settings'],
}


