import { useState, useEffect } from 'react'
import { fetchCorrelation } from '../api.js'

function kolorKorelacji(v) {
  if (v === null) return '#2a2d3a'
  if (v >= 0.8)  return '#c0392b'
  if (v >= 0.6)  return '#e67e22'
  if (v >= 0.4)  return '#f1c40f'
  if (v >= 0.2)  return '#27ae60'
  if (v >= -0.2) return '#2ecc71'
  if (v >= -0.5) return '#2980b9'
  return '#1a5276'
}

function opisKorelacji(v) {
  if (v === null) return '—'
  if (v >= 0.8)  return 'Bardzo wysoka — duże ryzyko koncentracji'
  if (v >= 0.6)  return 'Wysoka — umiarkowane ryzyko'
  if (v >= 0.4)  return 'Umiarkowana'
  if (v >= 0.2)  return 'Niska — dobra dywersyfikacja'
  if (v >= -0.2) return 'Brak korelacji — bardzo dobra dywersyfikacja'
  return 'Ujemna — świetny hedging'
}

export default function CorrelationPage() {
  const [data, setData] = useState(null)
  const [hovered, setHovered] = useState(null)

  useEffect(() => { fetchCorrelation().then(setData) }, [])

  if (!data) return <div style={{ color: '#666', padding: 40, textAlign: 'center' }}>Obliczanie korelacji (może potrwać chwilę)...</div>
  if (data.error) return <div style={{ color: '#e74c3c', padding: 20 }}>Błąd: {data.error}</div>

  const { symbole, nazwy, markety, macierz, wysokie_pary } = data
  const n = symbole.length
  const cellSize = Math.min(64, Math.floor((Math.min(900, window.innerWidth - 80) - 140) / n))
  const labelW = 130

  return (
    <div style={{ color: '#fff' }}>
      <div style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 6 }}>Analiza korelacji portfela</div>
      <div style={{ color: '#666', fontSize: 13, marginBottom: 24 }}>
        Dane dzienne z ostatnich 12 miesięcy. Wyższa korelacja = spółki poruszają się razem = większe ryzyko koncentracji.
      </div>

      {/* Heatmapa */}
      <div style={{ overflowX: 'auto', marginBottom: 32 }}>
        <div style={{ display: 'inline-block', minWidth: labelW + n * cellSize + 16 }}>
          {/* Nagłówki kolumn */}
          <div style={{ display: 'flex', marginLeft: labelW, marginBottom: 4 }}>
            {symbole.map((s, j) => (
              <div key={j} style={{ width: cellSize, textAlign: 'center', fontSize: 10, color: markety[s] === 'usa' ? '#3498db' : '#aaa', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {s.replace('.WA', '')}
              </div>
            ))}
          </div>

          {/* Wiersze */}
          {symbole.map((s1, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', marginBottom: 2 }}>
              <div style={{ width: labelW, fontSize: 11, color: markety[s1] === 'usa' ? '#3498db' : '#aaa', paddingRight: 8, textAlign: 'right', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {nazwy[s1]}
              </div>
              {symbole.map((s2, j) => {
                const val = macierz[i][j]
                const isHov = hovered && hovered.i === i && hovered.j === j
                return (
                  <div key={j}
                    onMouseEnter={() => setHovered({ i, j, val, s1, s2 })}
                    onMouseLeave={() => setHovered(null)}
                    style={{
                      width: cellSize, height: cellSize,
                      background: kolorKorelacji(val),
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      fontSize: cellSize > 48 ? 11 : 9,
                      color: val !== null && Math.abs(val) > 0.3 ? '#000' : '#fff',
                      fontWeight: 'bold',
                      cursor: 'default',
                      border: isHov ? '2px solid #fff' : '2px solid transparent',
                      borderRadius: 3,
                      opacity: i === j ? 0.4 : 1,
                      boxSizing: 'border-box',
                    }}>
                    {val !== null ? val.toFixed(2) : ''}
                  </div>
                )
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Tooltip */}
      {hovered && hovered.i !== hovered.j && (
        <div style={{ background: '#1a1d27', border: '1px solid #2a2d3a', borderRadius: 8, padding: '12px 16px', marginBottom: 24, fontSize: 13 }}>
          <span style={{ color: '#fff', fontWeight: 'bold' }}>{nazwy[hovered.s1]}</span>
          <span style={{ color: '#666', margin: '0 8px' }}>↔</span>
          <span style={{ color: '#fff', fontWeight: 'bold' }}>{nazwy[hovered.s2]}</span>
          <span style={{ color: '#888', marginLeft: 16 }}>korelacja: </span>
          <span style={{ color: kolorKorelacji(hovered.val), fontWeight: 'bold' }}>{hovered.val?.toFixed(3)}</span>
          <span style={{ color: '#555', marginLeft: 12 }}>{opisKorelacji(hovered.val)}</span>
        </div>
      )}

      {/* Legenda */}
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 32, fontSize: 12 }}>
        {[
          ['#c0392b', '≥ 0.8 Bardzo wysoka'],
          ['#e67e22', '≥ 0.6 Wysoka'],
          ['#f1c40f', '≥ 0.4 Umiarkowana'],
          ['#27ae60', '≥ 0.2 Niska'],
          ['#2ecc71', '< 0.2 Brak'],
          ['#2980b9', '< -0.2 Ujemna'],
        ].map(([col, label]) => (
          <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <div style={{ width: 14, height: 14, background: col, borderRadius: 2 }} />
            <span style={{ color: '#888' }}>{label}</span>
          </div>
        ))}
      </div>

      {/* Ostrzeżenia ryzyka */}
      {wysokie_pary.length > 0 && (
        <div style={{ marginBottom: 24 }}>
          <div style={{ fontSize: 15, fontWeight: 'bold', marginBottom: 12, color: '#e74c3c' }}>
            ⚠ Koncentracja ryzyka — pary z korelacją ≥ 0.7
          </div>
          {wysokie_pary.map((p, i) => (
            <div key={i} style={{ background: '#1a1d27', border: '1px solid #3a1a1a', borderRadius: 8, padding: '10px 16px', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 16, fontSize: 13 }}>
              <span style={{ color: '#e74c3c', fontWeight: 'bold', minWidth: 48 }}>{p.korelacja.toFixed(2)}</span>
              <span style={{ color: '#fff' }}>{p.nazwa1}</span>
              <span style={{ color: '#444' }}>↔</span>
              <span style={{ color: '#fff' }}>{p.nazwa2}</span>
              <span style={{ color: '#555', marginLeft: 'auto', fontSize: 11 }}>{opisKorelacji(p.korelacja)}</span>
            </div>
          ))}
        </div>
      )}

      {wysokie_pary.length === 0 && (
        <div style={{ background: '#1a3a2a', border: '1px solid #26c281', borderRadius: 8, padding: '12px 16px', color: '#26c281', fontSize: 13 }}>
          Brak par z korelacją ≥ 0.7 — portfel jest dobrze zdywersyfikowany.
        </div>
      )}
    </div>
  )
}
