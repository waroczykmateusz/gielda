import { useState, useEffect } from 'react'
import { fetchChart } from '../api.js'
import StockChart from './StockChart.jsx'

const st = {
  container: { background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: 12, padding: 20, flex: 1, minWidth: 0 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 },
  close: { background: 'transparent', border: '1px solid #2a2d3a', color: '#888', padding: '4px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 12 },
  row: { display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '6px 0', borderBottom: '1px solid #2a2d3a' },
  grid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 20 },
  label: { color: '#777' },
  val: { fontWeight: 600 },
  tag: { display: 'inline-block', padding: '3px 8px', borderRadius: 4, margin: 2, fontSize: 12 },
  badge: { background: '#13151f', padding: '3px 8px', borderRadius: 4, fontSize: 11 },
  indicators: { display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 18 },
  sectionTitle: { color: '#666', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 10, marginTop: 4 },
}

export default function StockDetail({ s, waluta, onClose }) {
  const [chart, setChart] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setChart(null)
    fetchChart(s.symbol).then(d => {
      setChart(d)
      setLoading(false)
    })
  }, [s.symbol])

  const plusZ = s.zysk >= 0
  const plusC = s.zmiana_proc >= 0
  const histPlus = s.macd_hist_w > 0

  return (
    <div style={st.container}>
      <div style={st.header}>
        <div>
          <h2 style={{ fontSize: 20, color: '#fff', margin: 0 }}>{s.nazwa}</h2>
          <div style={{ fontSize: 12, color: '#555', marginTop: 2 }}>{s.symbol}</div>
        </div>
        <button style={st.close} onClick={onClose}>✕ zamknij</button>
      </div>

      <div style={{ display: 'flex', alignItems: 'baseline', gap: 16, marginBottom: 20 }}>
        <div style={{ fontSize: 36, fontWeight: 'bold', color: '#fff' }}>{s.cena} {waluta}</div>
        <div style={{ fontSize: 14, color: plusC ? '#26c281' : '#e74c3c' }}>{plusC ? '+' : ''}{s.zmiana_proc}% dziś</div>
      </div>

      <div style={st.grid}>
        <div>
          <div style={st.sectionTitle}>Pozycja</div>
          {[
            ['Liczba akcji', s.akcje],
            ['Śr. cena zakupu', `${s.srednia} ${waluta}`],
            ['Wartość pozycji', `${s.wartosc} ${waluta}`],
            ['Zysk / Strata', <span style={{ color: plusZ ? '#26c281' : '#e74c3c' }}>{s.zysk} {waluta} ({s.zysk_proc}%)</span>],
          ].map(([label, val]) => (
            <div key={label} style={st.row}>
              <span style={st.label}>{label}</span>
              <span style={st.val}>{val}</span>
            </div>
          ))}
        </div>

        <div>
          <div style={st.sectionTitle}>Alerty</div>
          <div style={{ marginBottom: 10 }}>
            {s.alert_up
              ? <span style={{ ...st.tag, background: '#1a3a2a', color: '#26c281' }}>powyżej: {s.alert_up} {waluta}</span>
              : <span style={{ ...st.tag, background: '#13151f', color: '#444' }}>brak alertu powyżej</span>}
          </div>
          <div>
            {s.alert_down
              ? <span style={{ ...st.tag, background: '#3a1a1a', color: '#e74c3c' }}>poniżej: {s.alert_down} {waluta}</span>
              : <span style={{ ...st.tag, background: '#13151f', color: '#444' }}>brak alertu poniżej</span>}
          </div>

          <div style={{ ...st.sectionTitle, marginTop: 16 }}>Wskaźniki techniczne</div>
          <div style={st.indicators}>
            <span style={{ ...st.badge, color: '#666' }}>RSI D: {s.rsi_d}</span>
            <span style={{ ...st.badge, color: '#aaa', fontWeight: 'bold' }}>RSI W: {s.rsi_w}</span>
            <span style={{ ...st.badge, color: '#666' }}>MACD: {s.macd_w}</span>
            <span style={{ ...st.badge, color: '#666' }}>Sygnał: {s.macd_signal_w}</span>
            <span style={{ ...st.badge, color: histPlus ? '#26c281' : '#e74c3c', fontWeight: 'bold' }}>
              Hist: {histPlus ? '+' : ''}{s.macd_hist_w} {histPlus ? '▲' : '▼'}
            </span>
          </div>
        </div>
      </div>

      {s.sygnaly && s.sygnaly.length > 0 && (
        <div style={{ marginBottom: 20 }}>
          <div style={st.sectionTitle}>Aktywne sygnały</div>
          {s.sygnaly.map((sg, i) => (
            <div key={i} style={{ background: '#13151f', borderRadius: 6, padding: '6px 10px', margin: '4px 0', fontSize: 12, borderLeft: `3px solid ${sg.kolor}` }}>
              <span style={{ color: sg.kolor, fontWeight: 'bold' }}>{sg.typ}</span>
              <span style={{ color: '#aaa' }}> — {sg.opis}</span>
            </div>
          ))}
        </div>
      )}

      <div style={st.sectionTitle}>Wykres — 6 miesięcy</div>
      {loading && <div style={{ color: '#666', padding: 40, textAlign: 'center' }}>Ładowanie wykresu...</div>}
      {!loading && chart && chart.error && <div style={{ color: '#e74c3c', padding: 20 }}>Błąd: {chart.error}</div>}
      {!loading && chart && !chart.error && <StockChart data={chart} />}
    </div>
  )
}
