const st = {
  card: { background: '#1a1d27', borderRadius: 12, padding: 24, minWidth: 280, flex: 1, border: '1px solid #2a2d3a' },
  row: { display: 'flex', justifyContent: 'space-between', fontSize: 13, padding: '6px 0', borderBottom: '1px solid #2a2d3a' },
  label: { color: '#777' },
  val: { fontWeight: 600 },
  tag: { display: 'inline-block', padding: '3px 8px', borderRadius: 4, margin: 2, fontSize: 12 },
  indicators: { marginTop: 8, display: 'flex', gap: 8, fontSize: 11, flexWrap: 'wrap' },
  badge: { background: '#13151f', padding: '3px 8px', borderRadius: 4 },
}

export default function StockCard({ s, waluta }) {
  const plusZ = s.zysk >= 0
  const plusC = s.zmiana_proc >= 0
  const histPlus = s.macd_hist_w > 0

  return (
    <div style={st.card}>
      <h2 style={{ fontSize: 16, color: '#aaa', marginBottom: 4 }}>{s.nazwa}</h2>
      <div style={{ fontSize: 12, color: '#555', marginBottom: 16 }}>{s.symbol}</div>
      <div style={{ fontSize: 36, fontWeight: 'bold', marginBottom: 4 }}>{s.cena} {waluta}</div>
      <div style={{ fontSize: 14, marginBottom: 20, color: plusC ? '#26c281' : '#e74c3c' }}>{s.zmiana_proc}% dziś</div>

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

      <div style={{ marginTop: 16, fontSize: 12 }}>
        {s.alert_up
          ? <span style={{ ...st.tag, background: '#1a3a2a', color: '#26c281' }}>alert powyżej: {s.alert_up} {waluta}</span>
          : <span style={{ ...st.tag, background: '#1a1d27', color: '#444' }}>brak alertu powyżej</span>}
        {s.alert_down
          ? <span style={{ ...st.tag, background: '#3a1a1a', color: '#e74c3c' }}>alert poniżej: {s.alert_down} {waluta}</span>
          : <span style={{ ...st.tag, background: '#1a1d27', color: '#444' }}>brak alertu poniżej</span>}
      </div>

      {s.sygnaly.length > 0 && (
        <div style={{ marginTop: 10 }}>
          {s.sygnaly.map((sg, i) => (
            <div key={i} style={{ background: '#13151f', borderRadius: 6, padding: '6px 10px', margin: '4px 0', fontSize: 12, borderLeft: `3px solid ${sg.kolor}` }}>
              <span style={{ color: sg.kolor, fontWeight: 'bold' }}>{sg.typ}</span>
              <span style={{ color: '#aaa' }}> — {sg.opis}</span>
            </div>
          ))}
        </div>
      )}

      <div style={st.indicators}>
        <span style={{ ...st.badge, color: '#666' }}>RSI D: {s.rsi_d}</span>
        <span style={{ ...st.badge, color: '#aaa', fontWeight: 'bold' }}>RSI W: {s.rsi_w}</span>
        <span style={{ ...st.badge, color: '#666' }}>MACD: {s.macd_w}</span>
        <span style={{ ...st.badge, color: '#666' }}>Syg: {s.macd_signal_w}</span>
        <span style={{ ...st.badge, color: histPlus ? '#26c281' : '#e74c3c', fontWeight: 'bold' }}>
          Hist: {histPlus ? '+' : ''}{s.macd_hist_w} {histPlus ? '▲' : '▼'}
        </span>
      </div>
    </div>
  )
}
