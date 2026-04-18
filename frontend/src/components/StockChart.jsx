import { useState } from 'react'

const W = 800
const H_PRICE = 320
const H_RSI = 80
const H_MACD = 100
const GAP = 14
const PAD_L = 50
const PAD_R = 20
const PAD_T = 10
const PAD_B = 24

const COL = {
  price: '#ffffff',
  sma20: '#3498db',
  sma50: '#f1c40f',
  sma200: '#9b59b6',
  grid: '#2a2d3a',
  axis: '#555',
  rsi: '#e67e22',
  rsiRef: '#3a3d4a',
  macd: '#3498db',
  macdSig: '#e74c3c',
  histPos: '#26c281',
  histNeg: '#e74c3c',
}

export default function StockChart({ data }) {
  const [hover, setHover] = useState(null)

  if (!data || !data.punkty || data.punkty.length < 2) {
    return <div style={{ color: '#666', padding: 40, textAlign: 'center' }}>Brak danych do wyświetlenia wykresu.</div>
  }

  const pts = data.punkty
  const n = pts.length

  const closeVals = pts.map(p => p.close).filter(v => v != null)
  const sma20Vals = pts.map(p => p.sma20).filter(v => v != null)
  const sma50Vals = pts.map(p => p.sma50).filter(v => v != null)
  const sma200Vals = pts.map(p => p.sma200).filter(v => v != null)
  const allPriceVals = [...closeVals, ...sma20Vals, ...sma50Vals, ...sma200Vals]
  const pMin = Math.min(...allPriceVals)
  const pMax = Math.max(...allPriceVals)
  const pRange = pMax - pMin || 1
  const pPad = pRange * 0.05

  const macdVals = pts.map(p => p.macd).filter(v => v != null)
  const sigVals = pts.map(p => p.macd_signal).filter(v => v != null)
  const histVals = pts.map(p => p.macd_hist).filter(v => v != null)
  const macdAll = [...macdVals, ...sigVals, ...histVals]
  const mMin = Math.min(...macdAll, 0)
  const mMax = Math.max(...macdAll, 0)
  const mRange = mMax - mMin || 1

  const priceY0 = PAD_T
  const priceY1 = priceY0 + H_PRICE
  const rsiY0 = priceY1 + GAP
  const rsiY1 = rsiY0 + H_RSI
  const macdY0 = rsiY1 + GAP
  const macdY1 = macdY0 + H_MACD
  const totalH = macdY1 + PAD_B

  const xOf = i => PAD_L + (i / (n - 1)) * (W - PAD_L - PAD_R)
  const yPrice = v => priceY1 - ((v - (pMin - pPad)) / (pRange + 2 * pPad)) * H_PRICE
  const yRsi = v => rsiY1 - (v / 100) * H_RSI
  const yMacd = v => macdY1 - ((v - mMin) / mRange) * H_MACD

  const linePath = (field, yFn) => {
    let d = ''
    let started = false
    pts.forEach((p, i) => {
      if (p[field] == null) return
      const x = xOf(i)
      const y = yFn(p[field])
      d += started ? ` L ${x} ${y}` : `M ${x} ${y}`
      started = true
    })
    return d
  }

  const priceTicks = 5
  const yTicks = Array.from({ length: priceTicks + 1 }, (_, i) => {
    const v = pMin - pPad + (pRange + 2 * pPad) * (i / priceTicks)
    return { y: yPrice(v), label: v.toFixed(2) }
  })

  const xTickCount = 6
  const xTicks = Array.from({ length: xTickCount }, (_, i) => {
    const idx = Math.round((n - 1) * (i / (xTickCount - 1)))
    return { x: xOf(idx), label: pts[idx].date.slice(5) }
  })

  const barW = Math.max(1, (W - PAD_L - PAD_R) / n * 0.7)
  const zeroMacdY = yMacd(0)

  const markerMap = {}
  for (const m of (data.markery || [])) {
    markerMap[m.date] = markerMap[m.date] || []
    markerMap[m.date].push(m)
  }

  const lastIdx = pts.length - 1

  return (
    <div style={{ width: '100%', overflowX: 'auto' }}>
      <svg viewBox={`0 0 ${W} ${totalH}`} style={{ width: '100%', maxWidth: W, display: 'block', background: '#13151f', borderRadius: 8, border: '1px solid #2a2d3a' }}>
        {yTicks.map((t, i) => (
          <g key={`py${i}`}>
            <line x1={PAD_L} y1={t.y} x2={W - PAD_R} y2={t.y} stroke={COL.grid} strokeDasharray="2 3" />
            <text x={PAD_L - 6} y={t.y + 3} textAnchor="end" fill={COL.axis} fontSize="10">{t.label}</text>
          </g>
        ))}
        {xTicks.map((t, i) => (
          <text key={`x${i}`} x={t.x} y={macdY1 + 16} textAnchor="middle" fill={COL.axis} fontSize="10">{t.label}</text>
        ))}

        <path d={linePath('sma200', yPrice)} fill="none" stroke={COL.sma200} strokeWidth="1.2" opacity="0.8" />
        <path d={linePath('sma50', yPrice)} fill="none" stroke={COL.sma50} strokeWidth="1.2" opacity="0.8" />
        <path d={linePath('sma20', yPrice)} fill="none" stroke={COL.sma20} strokeWidth="1.2" opacity="0.8" />
        <path d={linePath('close', yPrice)} fill="none" stroke={COL.price} strokeWidth="1.8" />

        {(data.markery || []).map((m, i) => {
          const idx = pts.findIndex(p => p.date === m.date)
          if (idx === -1 || m.price == null) return null
          const x = xOf(idx)
          const y = yPrice(m.price)
          const up = m.kolor === '#26c281'
          const tri = up
            ? `${x},${y + 18} ${x - 6},${y + 28} ${x + 6},${y + 28}`
            : `${x},${y - 18} ${x - 6},${y - 28} ${x + 6},${y - 28}`
          return (
            <g key={`m${i}`}>
              <polygon points={tri} fill={m.kolor} opacity="0.9" />
            </g>
          )
        })}

        <line x1={PAD_L} y1={yRsi(30)} x2={W - PAD_R} y2={yRsi(30)} stroke={COL.rsiRef} strokeDasharray="3 3" />
        <line x1={PAD_L} y1={yRsi(70)} x2={W - PAD_R} y2={yRsi(70)} stroke={COL.rsiRef} strokeDasharray="3 3" />
        <text x={PAD_L - 6} y={yRsi(30) + 3} textAnchor="end" fill={COL.axis} fontSize="9">30</text>
        <text x={PAD_L - 6} y={yRsi(70) + 3} textAnchor="end" fill={COL.axis} fontSize="9">70</text>
        <text x={PAD_L - 6} y={rsiY0 + 10} textAnchor="end" fill={COL.axis} fontSize="9">RSI</text>
        <path d={linePath('rsi', yRsi)} fill="none" stroke={COL.rsi} strokeWidth="1.3" />

        <line x1={PAD_L} y1={zeroMacdY} x2={W - PAD_R} y2={zeroMacdY} stroke={COL.rsiRef} />
        <text x={PAD_L - 6} y={macdY0 + 10} textAnchor="end" fill={COL.axis} fontSize="9">MACD</text>
        {pts.map((p, i) => {
          if (p.macd_hist == null) return null
          const x = xOf(i)
          const y = yMacd(p.macd_hist)
          const isPos = p.macd_hist >= 0
          return (
            <rect key={`h${i}`}
              x={x - barW / 2}
              y={Math.min(y, zeroMacdY)}
              width={barW}
              height={Math.abs(y - zeroMacdY)}
              fill={isPos ? COL.histPos : COL.histNeg}
              opacity="0.5" />
          )
        })}
        <path d={linePath('macd_signal', yMacd)} fill="none" stroke={COL.macdSig} strokeWidth="1.2" />
        <path d={linePath('macd', yMacd)} fill="none" stroke={COL.macd} strokeWidth="1.2" />

        <rect x={PAD_L} y={priceY0} width={W - PAD_L - PAD_R} height={H_PRICE + GAP + H_RSI + GAP + H_MACD}
          fill="transparent"
          onMouseMove={e => {
            const rect = e.currentTarget.getBoundingClientRect()
            const rel = (e.clientX - rect.left) / rect.width
            const xAbs = PAD_L + rel * (W - PAD_L - PAD_R)
            const idx = Math.round((xAbs - PAD_L) / (W - PAD_L - PAD_R) * (n - 1))
            if (idx >= 0 && idx < n) setHover(idx)
          }}
          onMouseLeave={() => setHover(null)} />

        {hover != null && (
          <g>
            <line x1={xOf(hover)} y1={priceY0} x2={xOf(hover)} y2={macdY1} stroke="#fff" strokeDasharray="2 4" opacity="0.3" />
          </g>
        )}
      </svg>

      <div style={{ display: 'flex', gap: 16, marginTop: 10, fontSize: 11, flexWrap: 'wrap' }}>
        <Legend color={COL.price} label="Cena" />
        <Legend color={COL.sma20} label="SMA20" />
        <Legend color={COL.sma50} label="SMA50" />
        <Legend color={COL.sma200} label="SMA200" />
        <Legend color="#26c281" label="▲ sygnał kupna" />
        <Legend color="#e74c3c" label="▼ ostrzeżenie" />
      </div>

      {hover != null && (
        <div style={{ marginTop: 10, background: '#1a1d27', padding: '8px 12px', borderRadius: 6, fontSize: 12, color: '#aaa', display: 'flex', gap: 14, flexWrap: 'wrap' }}>
          <span style={{ color: '#fff' }}>{pts[hover].date}</span>
          {pts[hover].close != null && <span>close <b style={{ color: '#fff' }}>{pts[hover].close}</b></span>}
          {pts[hover].sma20 != null && <span style={{ color: COL.sma20 }}>SMA20 {pts[hover].sma20}</span>}
          {pts[hover].sma50 != null && <span style={{ color: COL.sma50 }}>SMA50 {pts[hover].sma50}</span>}
          {pts[hover].sma200 != null && <span style={{ color: COL.sma200 }}>SMA200 {pts[hover].sma200}</span>}
          {pts[hover].rsi != null && <span style={{ color: COL.rsi }}>RSI {pts[hover].rsi}</span>}
          {pts[hover].macd != null && <span style={{ color: COL.macd }}>MACD {pts[hover].macd}</span>}
        </div>
      )}

      {data.markery && data.markery.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <div style={{ color: '#666', fontSize: 11, textTransform: 'uppercase', marginBottom: 6 }}>Ostatnie sygnały ({data.markery.length})</div>
          <div style={{ maxHeight: 140, overflowY: 'auto' }}>
            {[...data.markery].reverse().slice(0, 10).map((m, i) => (
              <div key={i} style={{ padding: '4px 8px', fontSize: 11, borderLeft: `3px solid ${m.kolor}`, background: '#13151f', marginBottom: 3, borderRadius: 4 }}>
                <span style={{ color: '#666' }}>{m.date}</span>
                <span style={{ color: m.kolor, marginLeft: 8, fontWeight: 'bold' }}>{m.typ}</span>
                <span style={{ color: '#aaa', marginLeft: 6 }}>{m.opis}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function Legend({ color, label }) {
  return (
    <span style={{ color: '#888', display: 'flex', alignItems: 'center', gap: 4 }}>
      <span style={{ width: 12, height: 2, background: color, display: 'inline-block' }} />
      {label}
    </span>
  )
}
