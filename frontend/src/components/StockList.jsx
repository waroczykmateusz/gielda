const st = {
  container: { background: '#13151f', border: '1px solid #2a2d3a', borderRadius: 8, padding: 8, width: 240, flexShrink: 0 },
  header: { color: '#666', fontSize: 11, textTransform: 'uppercase', letterSpacing: 1, padding: '8px 12px 10px', borderBottom: '1px solid #2a2d3a' },
  item: { padding: '10px 12px', borderRadius: 6, cursor: 'pointer', marginTop: 4, display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 },
  itemActive: { background: '#1a1d27' },
  left: { minWidth: 0 },
  nazwa: { color: '#ddd', fontSize: 13, fontWeight: 'bold', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' },
  symbol: { color: '#555', fontSize: 11 },
  right: { textAlign: 'right' },
  cena: { color: '#aaa', fontSize: 12, fontWeight: 'bold' },
}

export default function StockList({ spolki, selected, onSelect, waluta }) {
  return (
    <div style={st.container}>
      <div style={st.header}>Spółki ({spolki.length})</div>
      {spolki.map(s => {
        const plusC = s.zmiana_proc >= 0
        const active = selected === s.symbol
        return (
          <div key={s.symbol}
            onClick={() => onSelect(s.symbol)}
            onMouseEnter={e => { if (!active) e.currentTarget.style.background = '#171924' }}
            onMouseLeave={e => { if (!active) e.currentTarget.style.background = 'transparent' }}
            style={{ ...st.item, ...(active ? st.itemActive : {}) }}>
            <div style={st.left}>
              <div style={st.nazwa}>{s.nazwa}</div>
              <div style={st.symbol}>{s.symbol}</div>
            </div>
            <div style={st.right}>
              <div style={st.cena}>{s.cena} {waluta}</div>
              <div style={{ fontSize: 11, color: plusC ? '#26c281' : '#e74c3c' }}>{plusC ? '+' : ''}{s.zmiana_proc}%</div>
            </div>
          </div>
        )
      })}
    </div>
  )
}
