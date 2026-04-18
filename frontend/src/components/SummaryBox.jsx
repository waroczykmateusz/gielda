const s = {
  wrap: { background: '#1a1d27', borderRadius: 12, padding: 24, border: '1px solid #2a2d3a', marginBottom: 30 },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))', gap: 16 },
  box: { background: '#13151f', borderRadius: 8, padding: 16 },
  label: { fontSize: 12, color: '#666', marginBottom: 6 },
  value: { fontSize: 20, fontWeight: 'bold' },
}

export default function SummaryBox({ podsumowanie: p, waluta }) {
  const plus = p.zysk >= 0
  const plusDzis = (p.zysk_dzis ?? 0) >= 0
  return (
    <div style={s.wrap}>
      <h2 style={{ fontSize: 16, color: '#aaa', marginBottom: 16 }}>Podsumowanie portfela</h2>
      <div style={s.grid}>
        <div style={s.box}><div style={s.label}>Wartość portfela</div><div style={s.value}>{p.wartosc} {waluta}</div></div>
        <div style={s.box}><div style={s.label}>Zainwestowano</div><div style={s.value}>{p.zainwestowano} {waluta}</div></div>
        <div style={s.box}><div style={s.label}>Zysk / Strata</div><div style={{ ...s.value, color: plus ? '#26c281' : '#e74c3c' }}>{p.zysk} {waluta}</div></div>
        <div style={s.box}><div style={s.label}>Zwrot</div><div style={{ ...s.value, color: plus ? '#26c281' : '#e74c3c' }}>{p.zwrot}%</div></div>
        <div style={s.box}><div style={s.label}>Dzisiaj</div><div style={{ ...s.value, color: plusDzis ? '#26c281' : '#e74c3c' }}>{(p.zysk_dzis ?? 0) >= 0 ? '+' : ''}{p.zysk_dzis} {waluta}</div></div>
      </div>
    </div>
  )
}
