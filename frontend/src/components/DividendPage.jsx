import { useState, useEffect } from 'react'
import { fetchDividends } from '../api.js'

const ROK = new Date().getFullYear()

const s = {
  container: { color: '#fff' },
  header: { fontSize: 20, fontWeight: 'bold', marginBottom: 20 },
  summaryRow: { display: 'flex', gap: 16, marginBottom: 30 },
  box: { background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: 8, padding: '16px 24px', minWidth: 200 },
  boxLabel: { color: '#666', fontSize: 12, marginBottom: 4 },
  boxValue: { fontSize: 22, fontWeight: 'bold', color: '#26c281' },
  section: { marginBottom: 32 },
  sectionTitle: { fontSize: 15, fontWeight: 'bold', color: '#aaa', marginBottom: 12, textTransform: 'uppercase', letterSpacing: 1 },
  table: { width: '100%', borderCollapse: 'collapse' },
  th: { textAlign: 'left', padding: '8px 12px', fontSize: 12, color: '#666', borderBottom: '1px solid #2a2d3a', fontWeight: 'normal' },
  td: { padding: '10px 12px', fontSize: 13, borderBottom: '1px solid #1e2130' },
  noDiv: { color: '#444' },
  loading: { color: '#666', padding: 40, textAlign: 'center' },
}

function fmt(val, suffix = '') {
  if (val == null) return <span style={s.noDiv}>—</span>
  return `${val}${suffix}`
}

export default function DividendPage() {
  const [data, setData] = useState(null)

  useEffect(() => {
    fetchDividends().then(setData)
  }, [])

  if (!data) return <div style={s.loading}>Ładowanie danych dywidendowych...</div>
  if (data.error) return <div style={{ color: '#e74c3c', padding: 20 }}>Błąd: {data.error}</div>

  const gpw = data.spolki.filter(s => s.market === 'gpw')
  const usa = data.spolki.filter(s => s.market === 'usa')

  return (
    <div style={s.container}>
      <div style={s.header}>Przewidywane dywidendy — {ROK}</div>

      <div style={s.summaryRow}>
        <div style={s.box}>
          <div style={s.boxLabel}>Łącznie GPW</div>
          <div style={s.boxValue}>{data.lacznie_gpw.toFixed(2)} zł</div>
        </div>
        <div style={s.box}>
          <div style={s.boxLabel}>Łącznie USA</div>
          <div style={s.boxValue}>{data.lacznie_usa.toFixed(2)} $</div>
        </div>
      </div>

      <DivTable title="GPW" spolki={gpw} waluta="zł" />
      <DivTable title="USA" spolki={usa} waluta="$" />
    </div>
  )
}

function DivTable({ title, spolki, waluta }) {
  if (!spolki.length) return null
  return (
    <div style={s.section}>
      <div style={s.sectionTitle}>{title}</div>
      <table style={s.table}>
        <thead>
          <tr>
            {['Spółka', 'Akcje', 'Dywidenda/akcję', `Łączna wypłata (${waluta})`, 'Yield %', 'Ex-date', 'Pay-date'].map(h => (
              <th key={h} style={s.th}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {spolki.map(sp => (
            <tr key={sp.symbol}>
              <td style={s.td}>
                <div style={{ fontWeight: 'bold' }}>{sp.nazwa}</div>
                <div style={{ color: '#666', fontSize: 11 }}>{sp.symbol}</div>
              </td>
              <td style={s.td}>{sp.akcje}</td>
              <td style={s.td}>{fmt(sp.dywidenda_na_akcje)}</td>
              <td style={{ ...s.td, color: sp.wyplata_laczna ? '#26c281' : undefined, fontWeight: sp.wyplata_laczna ? 'bold' : undefined }}>
                {fmt(sp.wyplata_laczna != null ? sp.wyplata_laczna.toFixed(2) : null)}
              </td>
              <td style={s.td}>{fmt(sp.yield_proc, '%')}</td>
              <td style={s.td}>{fmt(sp.ex_date)}</td>
              <td style={s.td}>{fmt(sp.pay_date)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
