import { useState, useEffect } from 'react'
import { fetchPortfolio, fetchCorrelation, fetchRecommendation } from '../api.js'

const st = {
  header: { fontSize: 20, fontWeight: 'bold', color: '#fff', marginBottom: 6 },
  sub: { color: '#666', fontSize: 13, marginBottom: 28 },
  summaryGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: 12, marginBottom: 28 },
  box: { background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: 8, padding: '14px 18px' },
  boxLabel: { color: '#666', fontSize: 11, marginBottom: 4 },
  boxVal: { fontSize: 18, fontWeight: 'bold' },
  btn: { background: '#26c281', color: '#000', border: 'none', borderRadius: 8, padding: '12px 28px', fontSize: 14, fontWeight: 'bold', cursor: 'pointer' },
  btnDisabled: { background: '#2a2d3a', color: '#555', border: 'none', borderRadius: 8, padding: '12px 28px', fontSize: 14, fontWeight: 'bold', cursor: 'not-allowed' },
  result: { background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: 12, padding: 24, marginTop: 24 },
  section: { marginBottom: 16 },
  sectionTitle: { color: '#26c281', fontWeight: 'bold', fontSize: 14, marginBottom: 8 },
  paragraph: { color: '#ccc', fontSize: 13, lineHeight: 1.7 },
  bullet: { color: '#ccc', fontSize: 13, lineHeight: 1.9, paddingLeft: 16 },
  priority: { background: '#13151f', border: '1px solid #26c281', borderRadius: 8, padding: '12px 16px', marginTop: 16, color: '#26c281', fontSize: 13, fontWeight: 'bold' },
  error: { color: '#e74c3c', padding: 20 },
  timestamp: { color: '#444', fontSize: 11, marginTop: 16 },
  refreshBtn: { background: 'transparent', border: '1px solid #2a2d3a', color: '#666', borderRadius: 6, padding: '6px 14px', fontSize: 12, cursor: 'pointer', marginLeft: 12 },
}

function renderRekomendacja(text) {
  if (!text) return null
  const sections = text.split(/\n(?=\*\*[A-ZĄĆĘŁŃÓŚŹŻ])/u)
  return sections.map((section, i) => {
    const lines = section.split('\n').filter(l => l.trim())
    const titleMatch = lines[0]?.match(/^\*\*(.+?)\*\*/)
    const title = titleMatch ? titleMatch[1] : null
    const rest = title ? lines.slice(1) : lines

    return (
      <div key={i} style={st.section}>
        {title && <div style={st.sectionTitle}>{title}</div>}
        {rest.map((line, j) => {
          const isBullet = /^[-•*]\s/.test(line.trim())
          const clean = line.replace(/\*\*(.*?)\*\*/g, '$1').replace(/^[-•*]\s/, '').trim()
          if (!clean) return null
          return isBullet
            ? <div key={j} style={st.bullet}>• {clean}</div>
            : <div key={j} style={st.paragraph}>{clean}</div>
        })}
      </div>
    )
  })
}

export default function RecommendationPage() {
  const [gpw, setGpw] = useState(null)
  const [usa, setUsa] = useState(null)
  const [korelacje, setKorelacje] = useState(null)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [timestamp, setTimestamp] = useState(null)
  const [dataReady, setDataReady] = useState(false)

  useEffect(() => {
    Promise.all([
      fetchPortfolio('gpw'),
      fetchPortfolio('usa'),
      fetchCorrelation(),
    ]).then(([g, u, k]) => {
      setGpw(g)
      setUsa(u)
      setKorelacje(k)
      setDataReady(true)
    })
  }, [])

  const generuj = async () => {
    setLoading(true)
    setResult(null)
    setError(null)
    try {
      const data = await fetchRecommendation(gpw, usa, korelacje)
      if (data.error) setError(data.error)
      else {
        setResult(data.rekomendacja)
        setTimestamp(new Date().toLocaleTimeString('pl-PL'))
      }
    } catch (e) {
      setError(String(e))
    } finally {
      setLoading(false)
    }
  }

  const gpwPod = gpw?.podsumowanie || {}
  const usaPod = usa?.podsumowanie || {}
  const gpwZwrot = gpwPod.zwrot ?? 0
  const usaZwrot = usaPod.zwrot ?? 0
  const wysokie = korelacje?.wysokie_pary?.length ?? 0

  return (
    <div style={{ color: '#fff', maxWidth: 860 }}>
      <div style={st.header}>Rekomendacja AI</div>
      <div style={st.sub}>Claude analizuje cały portfel — pozycje, sygnały techniczne, korelacje i ryzyko — i daje konkretne wskazówki.</div>

      <div style={st.summaryGrid}>
        <div style={st.box}>
          <div style={st.boxLabel}>Portfel GPW</div>
          <div style={{ ...st.boxVal, color: gpwZwrot >= 0 ? '#26c281' : '#e74c3c' }}>
            {gpwPod.wartosc ?? '…'} zł
          </div>
          <div style={{ fontSize: 12, color: gpwZwrot >= 0 ? '#26c281' : '#e74c3c', marginTop: 2 }}>
            {gpwZwrot >= 0 ? '+' : ''}{gpwZwrot}%
          </div>
        </div>
        <div style={st.box}>
          <div style={st.boxLabel}>Portfel USA</div>
          <div style={{ ...st.boxVal, color: usaZwrot >= 0 ? '#26c281' : '#e74c3c' }}>
            {usaPod.wartosc ?? '…'} $
          </div>
          <div style={{ fontSize: 12, color: usaZwrot >= 0 ? '#26c281' : '#e74c3c', marginTop: 2 }}>
            {usaZwrot >= 0 ? '+' : ''}{usaZwrot}%
          </div>
        </div>
        <div style={st.box}>
          <div style={st.boxLabel}>Spółek w portfelu</div>
          <div style={st.boxVal}>{(gpw?.spolki?.length ?? 0) + (usa?.spolki?.length ?? 0)}</div>
        </div>
        <div style={st.box}>
          <div style={st.boxLabel}>Pary wysokiej korelacji</div>
          <div style={{ ...st.boxVal, color: wysokie > 0 ? '#e74c3c' : '#26c281' }}>{dataReady ? wysokie : '…'}</div>
        </div>
      </div>

      <button
        style={!dataReady || loading ? st.btnDisabled : st.btn}
        disabled={!dataReady || loading}
        onClick={generuj}>
        {loading ? '⏳ Analizuję portfel...' : '✦ Generuj rekomendację AI'}
      </button>

      {error && <div style={st.error}>Błąd: {error}</div>}

      {result && (
        <div style={st.result}>
          <div style={{ color: '#888', fontSize: 12, marginBottom: 16 }}>Analiza wygenerowana przez Claude Sonnet</div>
          {renderRekomendacja(result)}
          <div style={st.timestamp}>
            Wygenerowano: {timestamp}
            <button style={st.refreshBtn} onClick={generuj}>↻ odśwież</button>
          </div>
        </div>
      )}
    </div>
  )
}
