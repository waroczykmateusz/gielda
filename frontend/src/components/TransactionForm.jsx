import { useState } from 'react'
import { addTransaction } from '../api.js'

const st = {
  wrap: { background: '#1a1d27', borderRadius: 12, padding: 24, border: '1px solid #2a2d3a', marginBottom: 30 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 12, alignItems: 'end' },
  group: { display: 'flex', flexDirection: 'column', gap: 6 },
  label: { fontSize: 12, color: '#666' },
  input: { background: '#13151f', border: '1px solid #2a2d3a', borderRadius: 6, padding: '8px 12px', color: '#e0e0e0', fontSize: 14 },
  btn: { background: '#26c281', color: '#000', border: 'none', borderRadius: 6, padding: '9px 20px', fontSize: 14, fontWeight: 'bold', cursor: 'pointer' },
}

export default function TransactionForm({ tab, waluta, onDone }) {
  const [form, setForm] = useState({ typ: 'kup', symbol: '', nazwa: '', akcje: '', cena: '' })
  const set = k => e => setForm(f => ({ ...f, [k]: e.target.value }))

  const submit = async e => {
    e.preventDefault()
    await addTransaction({ ...form, tab })
    setForm({ typ: 'kup', symbol: '', nazwa: '', akcje: '', cena: '' })
    onDone('Transakcja zapisana!')
  }

  return (
    <div style={st.wrap}>
      <h2 style={{ fontSize: 16, color: '#aaa', marginBottom: 16 }}>Dodaj transakcję {tab.toUpperCase()}</h2>
      <form onSubmit={submit}>
        <div style={st.grid}>
          <div style={st.group}>
            <label style={st.label}>Typ</label>
            <select style={st.input} value={form.typ} onChange={set('typ')}>
              <option value="kup">Kup</option>
              <option value="sprzedaj">Sprzedaj</option>
            </select>
          </div>
          <div style={st.group}>
            <label style={st.label}>Symbol</label>
            <input style={st.input} value={form.symbol} onChange={set('symbol')} placeholder={tab === 'gpw' ? 'ASB.WA' : 'RKLB'} required />
          </div>
          <div style={st.group}>
            <label style={st.label}>Nazwa spółki</label>
            <input style={st.input} value={form.nazwa} onChange={set('nazwa')} placeholder="Nazwa" />
          </div>
          <div style={st.group}>
            <label style={st.label}>Liczba akcji</label>
            <input style={st.input} type="number" min="1" value={form.akcje} onChange={set('akcje')} required />
          </div>
          <div style={st.group}>
            <label style={st.label}>Cena zakupu ({waluta})</label>
            <input style={st.input} type="number" step="0.01" min="0.01" value={form.cena} onChange={set('cena')} required />
          </div>
          <div style={st.group}>
            <button type="submit" style={st.btn}>Zapisz</button>
          </div>
        </div>
      </form>
    </div>
  )
}
