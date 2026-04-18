import { useState, useEffect } from 'react'
import { fetchPortfolio } from '../api.js'
import StockCard from './StockCard.jsx'
import SummaryBox from './SummaryBox.jsx'
import TransactionForm from './TransactionForm.jsx'
import AlertForm from './AlertForm.jsx'

export default function PortfolioTab({ tab, waluta }) {
  const [data, setData] = useState(null)
  const [msg, setMsg] = useState('')

  const load = () => fetchPortfolio(tab).then(setData)

  useEffect(() => { load() }, [tab])
  useEffect(() => { const id = setInterval(load, 60000); return () => clearInterval(id) }, [tab])

  if (!data) return <p style={{ color: '#666' }}>Ładowanie...</p>

  return (
    <div>
      {msg && <div style={{ padding: '10px 16px', borderRadius: 8, marginBottom: 20, background: '#1a3a2a', color: '#26c281', fontSize: 14 }}>{msg}</div>}
      <SummaryBox podsumowanie={data.podsumowanie} waluta={waluta} />
      <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap', marginBottom: 40 }}>
        {data.spolki.map(s => <StockCard key={s.symbol} s={s} waluta={waluta} />)}
      </div>
      <TransactionForm tab={tab} waluta={waluta} spolki={data.spolki} onDone={(m) => { setMsg(m); load() }} />
      <AlertForm tab={tab} waluta={waluta} spolki={data.spolki} onDone={(m) => { setMsg(m); load() }} />
      <p style={{ color: '#444', fontSize: 12, marginTop: 20 }}>
        {tab === 'gpw' ? 'GPW: pon-pt 9:00–17:05' : 'NYSE/NASDAQ: pon-pt 15:30–22:00 CET'}
      </p>
    </div>
  )
}
