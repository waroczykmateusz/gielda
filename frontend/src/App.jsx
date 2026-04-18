import { useState } from 'react'
import PortfolioTab from './components/PortfolioTab.jsx'
import BacktestPage from './components/BacktestPage.jsx'
import DividendPage from './components/DividendPage.jsx'
import CorrelationPage from './components/CorrelationPage.jsx'
import RecommendationPage from './components/RecommendationPage.jsx'

const styles = {
  tabs: { display: 'flex', gap: 4, marginBottom: 30 },
  tab: { padding: '10px 28px', borderRadius: '8px 8px 0 0', fontSize: 14, fontWeight: 'bold', cursor: 'pointer', border: '1px solid #2a2d3a', borderBottom: 'none', background: '#13151f', color: '#666', textDecoration: 'none' },
  tabActive: { background: '#1a1d27', color: '#fff' },
}

export default function App() {
  const [tab, setTab] = useState('gpw')

  return (
    <div>
      <h1 style={{ fontSize: 24, marginBottom: 6, color: '#fff' }}>Mój Portfel</h1>
      <p style={{ color: '#666', fontSize: 13, marginBottom: 20 }}>Odświeżenie co 60 sekund</p>

      <div style={styles.tabs}>
        {['gpw', 'usa', 'dywidendy', 'korelacja', 'rekomendacja', 'backtest'].map(t => (
          <button key={t} onClick={() => setTab(t)}
            style={{ ...styles.tab, ...(tab === t ? styles.tabActive : {}) }}>
            {t === 'gpw' ? 'GPW' : t === 'usa' ? 'USA' : t === 'dywidendy' ? 'Dywidendy' : t === 'korelacja' ? 'Korelacja' : t === 'rekomendacja' ? 'Rekomendacja AI' : 'Backtest'}
          </button>
        ))}
      </div>

      {tab === 'gpw' && <PortfolioTab tab="gpw" waluta="zł" />}
      {tab === 'usa' && <PortfolioTab tab="usa" waluta="$" />}
      {tab === 'dywidendy' && <DividendPage />}
      {tab === 'korelacja' && <CorrelationPage />}
      {tab === 'rekomendacja' && <RecommendationPage />}
      {tab === 'backtest' && <BacktestPage />}
    </div>
  )
}
