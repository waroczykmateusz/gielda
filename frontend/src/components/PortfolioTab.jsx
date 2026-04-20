import { useState, useEffect } from 'react'
import { fetchPortfolio } from '../api.js'
import StockCard from './StockCard.jsx'
import SummaryBox from './SummaryBox.jsx'
import TransactionForm from './TransactionForm.jsx'
import AlertForm from './AlertForm.jsx'
import StockList from './StockList.jsx'
import StockDetail from './StockDetail.jsx'

export default function PortfolioTab({ tab, waluta }) {
  const [data, setData] = useState(null)
  const [msg, setMsg] = useState('')
  const [selected, setSelected] = useState(null)
  const [lastRefresh, setLastRefresh] = useState(null)
  const [loading, setLoading] = useState(false)

  const load = () => {
    setLoading(true)
    fetchPortfolio(tab).then(d => { setData(d); setLastRefresh(new Date()); setLoading(false) })
  }

  useEffect(() => { load(); setSelected(null) }, [tab])
  useEffect(() => { const id = setInterval(load, 60000); return () => clearInterval(id) }, [tab])

  if (!data) return <p style={{ color: '#666' }}>Ładowanie...</p>

  const selectedStock = selected ? data.spolki.find(s => s.symbol === selected) : null

  return (
    <div>
      {msg && <div style={{ padding: '10px 16px', borderRadius: 8, marginBottom: 20, background: '#1a3a2a', color: '#26c281', fontSize: 14 }}>{msg}</div>}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
        <button
          onClick={load}
          disabled={loading}
          style={{ padding: '6px 14px', borderRadius: 6, border: '1px solid #333', background: loading ? '#222' : '#1a1a1a', color: loading ? '#555' : '#aaa', cursor: loading ? 'default' : 'pointer', fontSize: 13 }}
        >
          {loading ? 'Odświeżanie...' : 'Odśwież'}
        </button>
        {lastRefresh && (
          <span style={{ color: '#555', fontSize: 12 }}>
            Ostatnie odświeżenie: {lastRefresh.toLocaleTimeString('pl-PL')}
          </span>
        )}
      </div>
      <SummaryBox podsumowanie={data.podsumowanie} waluta={waluta} />

      <div style={{ display: 'flex', gap: 20, marginBottom: 40, alignItems: 'flex-start' }}>
        <StockList spolki={data.spolki} selected={selected} onSelect={setSelected} waluta={waluta} />

        <div style={{ flex: 1, minWidth: 0 }}>
          {selectedStock ? (
            <StockDetail s={selectedStock} waluta={waluta} tab={tab} onClose={() => setSelected(null)} onRefresh={(m) => { setMsg(m); load() }} />
          ) : (
            <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
              {data.spolki.map(s => (
                <div key={s.symbol} onClick={() => setSelected(s.symbol)} style={{ cursor: 'pointer', minWidth: 280, flex: 1 }}>
                  <StockCard s={s} waluta={waluta} tab={tab} onRefresh={(m) => { setMsg(m); load() }} />
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <TransactionForm tab={tab} waluta={waluta} spolki={data.spolki} onDone={(m) => { setMsg(m); load() }} />
      <AlertForm tab={tab} waluta={waluta} spolki={data.spolki} onDone={(m) => { setMsg(m); load() }} />
      <p style={{ color: '#444', fontSize: 12, marginTop: 20 }}>
        {tab === 'gpw' ? 'GPW: pon-pt 9:00–17:05' : 'NYSE/NASDAQ: pon-pt 15:30–22:00 CET'}
      </p>
    </div>
  )
}
