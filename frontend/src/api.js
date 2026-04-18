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

export async function fetchBacktest() {
  const res = await fetch(`${BASE}/backtest`)
  return res.json()
}
