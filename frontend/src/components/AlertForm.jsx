import { useState } from 'react'
import { setAlert } from '../api.js'

const st = {
  wrap: { background: '#1a1d27', borderRadius: 12, padding: 24, border: '1px solid #2a2d3a', marginBottom: 30 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, alignItems: 'end' },
  group: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 12, color: '#666' },
  input: { background: '#13151f', border: '1px solid #2a2d3a', borderRadius: 6, padding: '8px 12px', color: '#e0e0e0', fontSize: 14 },
  btn: { background: '#f39c12', color: '#000', border: 'none', borderRadius: 6, padding: '9px 20px', fontSize: 14, fontWeight: 'bold', cursor: 'pointer' },
}

export default function AlertForm({ tab, waluta, spolki, onDone }) {
  const [symbol, setSymbol] = useState(spolki[0]?.symbol || '')
  const [up, setUp] = useState('')
  const [down, setDown] = useState('')

  const submit = async e => {
    e.preventDefault()
    await setAlert({ tab, symbol, alert_powyzej: up ? parseFloat(up) : null, alert_ponizej: down ? parseFloat(down) : null })
    onDone(`Alert zapisany dla ${symbol}!`)
  }

  return (
    <div style={st.wrap}>
      <h2 style={{ fontSize: 16, color: '#aaa', marginBottom: 16 }}>Ustaw alert cenowy {tab.toUpperCase()}</h2>
      <form onSubmit={submit}>
        <div style={st.grid}>
          <div style={st.group}>
            <label style={st.label}>Spółka</label>
            <select style={st.input} value={symbol} onChange={e => setSymbol(e.target.value)}>
              {spolki.map(s => <option key={s.symbol} value={s.symbol}>{s.nazwa}</option>)}
            </select>
          </div>
          <div style={st.group}>
            <label style={st.label}>Alert powyżej ({waluta})</label>
            <input style={st.input} type="number" step="0.01" min="0" value={up} onChange={e => setUp(e.target.value)} placeholder="np. 200.00" />
          </div>
          <div style={st.group}>
            <label style={st.label}>Alert poniżej ({waluta})</label>
            <input style={st.input} type="number" step="0.01" min="0" value={down} onChange={e => setDown(e.target.value)} placeholder="np. 150.00" />
          </div>
          <div style={st.group}>
            <button type="submit" style={st.btn}>Zapisz alert</button>
          </div>
        </div>
      </form>
    </div>
  )
}
