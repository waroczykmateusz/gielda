export const config = {
  matcher: ['/((?!api/cron).*)'],
}

const EXPECTED = 'Basic ' + btoa('mati:53809')

export default function middleware(request) {
  if (request.headers.get('authorization') === EXPECTED) {
    return
  }
  return new Response('Unauthorized', {
    status: 401,
    headers: {
      'WWW-Authenticate': 'Basic realm="Mój Portfel GPW"',
      'Content-Type': 'text/plain',
    },
  })
}
