const BASE = '/api'

export async function fetchPortfolio(tab) {
  const res = await fetch(`${BASE}/portfolio/${tab}`)
  return res.json()
}

export async function addTransaction(data) {
  const res = await fetch(`${BASE}/transaction`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function setAlert(data) {
  const res = await fetch(`${BASE}/alert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })
  return res.json()
}

export async function fetchBacktest(symbol, market) {
  const params = new URLSearchParams({ symbol })
  if (market) params.set('market', market)
  const res = await fetch(`${BASE}/backtest?${params.toString()}`)
  return res.json()
}

export async function fetchDividends() {
  const res = await fetch(`${BASE}/dividends`)
  return res.json()
}

export async function clearAlert(tab, symbol) {
  const res = await fetch(`${BASE}/alert`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tab, symbol, alert_powyzej: null, alert_ponizej: null }),
  })
  return res.json()
}

export async function fetchRecommendation(gpw, usa, korelacje) {
  const res = await fetch(`${BASE}/recommendation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ gpw, usa, korelacje }),
  })
  return res.json()
}

export async function streamRecommendation(symbol, market, onChunk, onDone, onError) {
  try {
    const params = new URLSearchParams({ symbol, market })
    const res = await fetch(`${BASE}/recommend?${params.toString()}`)
    if (!res.ok) { onError(`HTTP ${res.status}`); return }

    const reader = res.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) { onDone(); break }

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop()

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const raw = line.slice(6)
        if (raw === '[DONE]') { onDone(); return }
        try {
          const parsed = JSON.parse(raw)
          if (parsed.error) { onError(parsed.error); return }
          if (parsed.text) onChunk(parsed.text)
        } catch {}
      }
    }
  } catch (e) {
    onError(e.message)
  }
}

export async function fetchCorrelation() {
  const res = await fetch(`${BASE}/correlation`)
  return res.json()
}

export async function fetchChart(symbol) {
  const params = new URLSearchParams({ symbol })
  const res = await fetch(`${BASE}/chart?${params.toString()}`)
  return res.json()
}

export async function fetchPortfolioSymbols() {
  const [gpw, usa] = await Promise.all([
    fetchPortfolio('gpw'),
    fetchPortfolio('usa'),
  ])
  const items = []
  for (const s of (gpw.spolki || [])) items.push({ symbol: s.symbol, nazwa: s.nazwa, market: 'gpw' })
  for (const s of (usa.spolki || [])) items.push({ symbol: s.symbol, nazwa: s.nazwa, market: 'usa' })
  return items
}
