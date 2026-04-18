export const config = {
  matcher: ['/((?!api/cron).*)'],
}

export default function middleware(request) {
  const user = process.env.AUTH_USER
  const pass = process.env.AUTH_PASS

  const auth = request.headers.get('authorization')
  if (auth && auth.startsWith('Basic ')) {
    try {
      const decoded = atob(auth.slice(6))
      const colon = decoded.indexOf(':')
      if (decoded.slice(0, colon) === user && decoded.slice(colon + 1) === pass) {
        return
      }
    } catch {}
  }

  return new Response('Unauthorized', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Mój Portfel GPW"',
      'Content-Type': 'text/plain',
    },
  })
}
