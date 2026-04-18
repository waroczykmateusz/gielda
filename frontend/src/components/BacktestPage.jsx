import { useState, useEffect } from 'react'
import { fetchBacktest, fetchPortfolioSymbols } from '../api.js'

const st = {
  spolka: { background: '#1a1d27', borderRadius: 12, padding: 24, marginBottom: 24, border: '1px solid #2a2d3a' },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 },
  sekcja: { marginBottom: 20 },
  h3: { fontSize: 14, color: '#aaa', marginBottom: 12, borderBottom: '1px solid #2a2d3a', paddingBottom: 6 },
  stats: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(120px, 1fr))', gap: 12, marginBottom: 16 },
  stat: { background: '#13151f', borderRadius: 8, padding: 12, textAlign: 'center' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { textAlign: 'left', padding: '8px 10px', color: '#666', borderBottom: '1px solid #2a2d3a', fontWeight: 'normal' },
  td: { padding: '8px 10px', borderBottom: '1px solid #1a1d27' },
  btn: {
    background: '#26c281', color: '#fff', border: 'none', borderRadius: 6,
    padding: '8px 16px', cursor: 'pointer', fontSize: 13, fontWeight: 'bold',
  },
  btnSecondary: {
    background: '#2a2d3a', color: '#fff', border: 'none', borderRadius: 6,
    padding: '8px 16px', cursor: 'pointer', fontSize: 13,
  },
  btnDisabled: {
    background: '#2a2d3a', color: '#666', border: 'none', borderRadius: 6,
    padding: '8px 16px', cursor: 'not-allowed', fontSize: 13,
  },
  toolbar: { display: 'flex', gap: 12, marginBottom: 24, alignItems: 'center' },
}

function colClass(v) { return v > 0 ? '#26c281' : '#e74c3c' }
function skutecznoscColor(v) { return v >= 60 ? '#26c281' : v >= 40 ? '#f39c12' : '#e74c3c' }

function StatBox({ label, value, color }) {
  return (
    <div style={st.stat}>
      <div style={{ fontSize: 11, color: '#666', marginBottom: 4 }}>{label}</div>
      <div style={{ fontSize: 18, fontWeight: 'bold', color }}>{value}</div>
    </div>
  )
}

function SignalTable({ sygnaly, cols }) {
  if (!sygnaly?.length) return <p style={{ color: '#444', fontStyle: 'italic', fontSize: 13 }}>Brak sygnałów w ostatnich 3 latach.</p>
  return (
    <table style={st.table}>
      <thead><tr>{cols.map(c => <th key={c} style={st.th}>{c}</th>)}</tr></thead>
      <tbody>
        {sygnaly.map((s, i) => (
          <tr key={i}>
            <td style={st.td}>{s.data}</td>
            <td style={st.td}>{s.cena}</td>
            {s.rsi !== undefined && <td style={{ ...st.td, color: '#f39c12' }}>{s.rsi}</td>}
            {s.macd !== undefined && <td style={{ ...st.td, color: '#4a9eff' }}>{s.macd}</td>}
            {s.strefa !== undefined && <td style={{ ...st.td, color: s.strefa === 'dodatnia' ? '#26c281' : '#f39c12' }}>{s.strefa}</td>}
            <td style={{ ...st.td, color: colClass(s.zysk_4t) }}>{s.zysk_4t}%</td>
            <td style={{ ...st.td, color: colClass(s.zysk_8t) }}>{s.zysk_8t}%</td>
            <td style={{ ...st.td, color: colClass(s.zysk_12t) }}>{s.zysk_12t}%</td>
            <td style={st.td}><span style={{ background: s.trafny ? '#1a3a2a' : '#3a1a1a', color: s.trafny ? '#26c281' : '#e74c3c', padding: '2px 8px', borderRadius: 4, fontSize: 11 }}>{s.trafny ? 'TRAFNY' : 'CHYBIONY'}</span></td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}

function Sekcja({ title, data, cols }) {
  const s = data.stats
  return (
    <div style={st.sekcja}>
      <h3 style={st.h3}>{title}</h3>
      {s.count > 0 ? (
        <>
          <div style={st.stats}>
            <StatBox label="Liczba sygnałów" value={s.count} color="#f39c12" />
            <StatBox label="Skuteczność" value={`${s.skutecznosc}%`} color={skutecznoscColor(s.skutecznosc)} />
            <StatBox label="Avg +4 tyg." value={`${s.avg_4t}%`} color={colClass(s.avg_4t)} />
            <StatBox label="Avg +8 tyg." value={`${s.avg_8t}%`} color={colClass(s.avg_8t)} />
            <StatBox label="Avg +12 tyg." value={`${s.avg_12t}%`} color={colClass(s.avg_12t)} />
          </div>
          <SignalTable sygnaly={data.sygnaly} cols={cols} />
        </>
      ) : <p style={{ color: '#444', fontStyle: 'italic', fontSize: 13 }}>Brak sygnałów w ostatnich 3 latach.</p>}
    </div>
  )
}

function SpolkaCard({ item, wynik, status, onRun }) {
  return (
    <div style={st.spolka}>
      <div style={st.header}>
        <h2 style={{ fontSize: 18, color: '#fff', margin: 0 }}>
          {item.nazwa} <span style={{ color: '#555', fontSize: 14 }}>{item.symbol}</span>
          <span style={{ color: '#444', fontSize: 12, marginLeft: 8 }}>[{item.market.toUpperCase()}]</span>
        </h2>
        <button
          style={status === 'loading' ? st.btnDisabled : st.btn}
          disabled={status === 'loading'}
          onClick={onRun}
        >
          {status === 'loading' ? '⏳ Liczenie...' : status === 'done' ? '↻ Ponów' : '▶ Uruchom backtest'}
        </button>
      </div>
      {status === 'error' && (
        <p style={{ color: '#e74c3c', fontSize: 13 }}>Błąd: {wynik?.error || 'nieznany'}</p>
      )}
      {status === 'done' && wynik && !wynik.error && (
        <>
          <Sekcja title="RSI tygodniowy < 40 (strefa wyprzedania)" data={wynik.rsi} cols={['Data', 'Cena', 'RSI tyg.', '+4 tyg.', '+8 tyg.', '+12 tyg.', 'Wynik']} />
          <Sekcja title="MACD tygodniowy — bullish crossover" data={wynik.macd} cols={['Data', 'Cena', 'MACD', 'Strefa', '+4 tyg.', '+8 tyg.', '+12 tyg.', 'Wynik']} />
          <Sekcja title="Złoty Krzyż SMA50/SMA200" data={wynik.sma} cols={['Data', 'Cena', '+4 tyg.', '+8 tyg.', '+12 tyg.', 'Wynik']} />
        </>
      )}
      {status === 'done' && wynik?.error && (
        <p style={{ color: '#e74c3c', fontSize: 13 }}>Brak danych: {wynik.error}</p>
      )}
    </div>
  )
}

export default function BacktestPage() {
  const [items, setItems] = useState(null)
  const [results, setResults] = useState({})
  const [statuses, setStatuses] = useState({})
  const [loadError, setLoadError] = useState(null)
  const [runningAll, setRunningAll] = useState(false)

  useEffect(() => {
    fetchPortfolioSymbols()
      .then(setItems)
      .catch(e => setLoadError(e.message))
  }, [])

  const runOne = async (item) => {
    const key = `${item.market}:${item.symbol}`
    setStatuses(s => ({ ...s, [key]: 'loading' }))
    try {
      const data = await fetchBacktest(item.symbol, item.market)
      setResults(r => ({ ...r, [key]: data }))
      setStatuses(s => ({ ...s, [key]: data?.error ? 'error' : 'done' }))
    } catch (e) {
      setResults(r => ({ ...r, [key]: { error: e.message } }))
      setStatuses(s => ({ ...s, [key]: 'error' }))
    }
  }

  const runAll = async () => {
    if (!items) return
    setRunningAll(true)
    for (const item of items) {
      await runOne(item)
    }
    setRunningAll(false)
  }

  if (loadError) return <p style={{ color: '#e74c3c', fontSize: 15, textAlign: 'center', padding: 60 }}>Błąd: {loadError}</p>
  if (!items) return <p style={{ color: '#444', fontSize: 16, textAlign: 'center', padding: 60 }}>⏳ Ładowanie listy spółek...</p>
  if (items.length === 0) return <p style={{ color: '#444', fontSize: 16, textAlign: 'center', padding: 60 }}>Brak spółek w portfelu.</p>

  return (
    <div>
      <h2 style={{ fontSize: 20, marginBottom: 8, color: '#fff' }}>Backtest strategii</h2>
      <p style={{ color: '#666', fontSize: 13, marginBottom: 24 }}>
        Analiza skuteczności sygnałów RSI/MACD tygodniowego i Złotego Krzyża — ostatnie 3 lata.
        Każda spółka liczona osobno (limit serverless). Kliknij <b>Uruchom backtest</b> przy spółce lub <b>Uruchom wszystkie</b> by przeliczyć po kolei.
      </p>
      <div style={st.toolbar}>
        <button
          style={runningAll ? st.btnDisabled : st.btnSecondary}
          disabled={runningAll}
          onClick={runAll}
        >
          {runningAll ? '⏳ Liczenie wszystkich...' : '▶ Uruchom wszystkie'}
        </button>
        <span style={{ color: '#666', fontSize: 12 }}>
          {items.length} spółek w portfelu
        </span>
      </div>
      {items.map(item => {
        const key = `${item.market}:${item.symbol}`
        return (
          <SpolkaCard
            key={key}
            item={item}
            wynik={results[key]}
            status={statuses[key]}
            onRun={() => runOne(item)}
          />
        )
      })}
    </div>
  )
}
