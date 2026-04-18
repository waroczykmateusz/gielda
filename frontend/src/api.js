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
