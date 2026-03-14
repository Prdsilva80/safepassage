import { useState, useEffect, useCallback, } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { reportsAPI, sheltersAPI } from '../services/api'
import { RefreshCw, X, AlertTriangle, Flame } from 'lucide-react'

const DANGER_COLORS = {
  critical: '#ff2b2b', high: '#ff6600', medium: '#ffb800', low: '#00cc66', safe: '#0088ff',
}

// Cor e raio do hotspot baseado no FRP (Fire Radiative Power em MW)
function frpStyle(frp, brightness) {
  if (frp > 50 || brightness > 400)  return { color: '#ff2b2b', radius: 10, opacity: 0.9 }
  if (frp > 20 || brightness > 360)  return { color: '#ff6600', radius: 8,  opacity: 0.8 }
  if (frp > 5  || brightness > 330)  return { color: '#ffb800', radius: 6,  opacity: 0.7 }
  return                                    { color: '#ff8c00', radius: 4,  opacity: 0.5 }
}

function ClickHandler({ onMapClick }) {
  useMapEvents({ click: (e) => onMapClick(e.latlng) })
  return null
}

function ReportModal({ latlng, onClose, onSubmit }) {
  const [form, setForm] = useState({
    report_type: 'armed_conflict', danger_level: 'high',
    title: '', description: '', lat: latlng.lat.toFixed(5), lng: latlng.lng.toFixed(5),
  })
  const [loading, setLoading] = useState(false)

  const submit = async () => {
    setLoading(true)
    try {
      await reportsAPI.create({ ...form, lat: parseFloat(form.lat), lng: parseFloat(form.lng) })
      onSubmit()
    } catch (e) { alert(e.response?.data?.detail || e.message) }
    finally { setLoading(false) }
  }

  const REPORT_TYPES = ['armed_conflict','airstrike','checkpoint','displaced_persons','medical_emergency','shelter_needed','road_blocked','safe_corridor']
  const DANGER_LEVELS = ['low','medium','high','critical']

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.8)',
      zIndex: 2000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
    }}>
      <div style={{
        background: 'var(--bg2)', border: '1px solid var(--border)',
        borderRadius: 8, padding: 24, width: '100%', maxWidth: 440,
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <h2 style={{ fontFamily: 'var(--mono)', fontSize: 14, letterSpacing: 2, color: 'var(--red)' }}>
            <AlertTriangle size={14} style={{ marginRight: 8, display: 'inline' }} />
            SUBMIT REPORT
          </h2>
          <button onClick={onClose} style={{ background: 'transparent', color: 'var(--text2)', padding: 4 }}>
            <X size={18} />
          </button>
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1, display: 'block', marginBottom: 4 }}>LAT</label>
            <input value={form.lat} onChange={e => setForm(f => ({ ...f, lat: e.target.value }))} />
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1, display: 'block', marginBottom: 4 }}>LNG</label>
            <input value={form.lng} onChange={e => setForm(f => ({ ...f, lng: e.target.value }))} />
          </div>
        </div>

        <div style={{ display: 'flex', gap: 8, marginBottom: 12 }}>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1, display: 'block', marginBottom: 4 }}>TYPE</label>
            <select value={form.report_type} onChange={e => setForm(f => ({ ...f, report_type: e.target.value }))}>
              {REPORT_TYPES.map(t => <option key={t} value={t}>{t.replace(/_/g, ' ').toUpperCase()}</option>)}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1, display: 'block', marginBottom: 4 }}>DANGER</label>
            <select value={form.danger_level} onChange={e => setForm(f => ({ ...f, danger_level: e.target.value }))}
              style={{ borderColor: DANGER_COLORS[form.danger_level] }}>
              {DANGER_LEVELS.map(l => <option key={l} value={l}>{l.toUpperCase()}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 12 }}>
          <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1, display: 'block', marginBottom: 4 }}>TITLE</label>
          <input value={form.title} onChange={e => setForm(f => ({ ...f, title: e.target.value }))} placeholder="Brief description" />
        </div>

        <div style={{ marginBottom: 20 }}>
          <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1, display: 'block', marginBottom: 4 }}>DETAILS (optional)</label>
          <textarea rows={3} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} placeholder="Additional details..." style={{ resize: 'vertical' }} />
        </div>

        <div style={{ display: 'flex', gap: 8 }}>
          <button onClick={onClose} style={{
            flex: 1, background: 'var(--bg3)', color: 'var(--text2)',
            padding: '10px', borderRadius: 4, fontFamily: 'var(--mono)', fontSize: 11,
            border: '1px solid var(--border)',
          }}>CANCEL</button>
          <button onClick={submit} disabled={loading || !form.title} style={{
            flex: 2, background: 'var(--red)', color: '#fff',
            padding: '10px', borderRadius: 4, fontFamily: 'var(--mono)', fontSize: 11,
            letterSpacing: 1, opacity: loading || !form.title ? 0.6 : 1,
          }}>{loading ? 'SUBMITTING...' : 'SUBMIT REPORT'}</button>
        </div>
      </div>
    </div>
  )
}

export default function MapPage() {
  const [reports, setReports]       = useState([])
  const [shelters, setShelters]     = useState([])
  const [hotspots, setHotspots]     = useState([])
  const [location, setLocation]     = useState(null)
  const [, setLoading]              = useState(false)
  const [firmsLoading, setFirmsLoading] = useState(false)
  const [radius, setRadius]         = useState(50)
  const [clickedLatlng, setClickedLatlng] = useState(null)
  const [mapCenter, setMapCenter]   = useState([48.5, 31.2])

  // Layers toggle
  const [showReports,   setShowReports]   = useState(true)
  const [showShelters,  setShowShelters]  = useState(true)
  const [showFIRMS,     setShowFIRMS]     = useState(true)
  const [firmsDays,     setFirmsDays]     = useState(1)
  const [firmsCountry,  setFirmsCountry]  = useState('Ukraine')

  const fetchData = useCallback(async (lat, lng) => {
    setLoading(true)
    try {
      const [r, s] = await Promise.all([
        reportsAPI.nearby(lat, lng, radius),
        sheltersAPI.nearby(lat, lng, radius),
      ])
      setReports(r.data)
      setShelters(s.data)
    } catch (e) { console.error(e) }
    finally { setLoading(false) }
  }, [radius])

  const fetchFIRMS = useCallback(async () => {
    setFirmsLoading(true)
    try {
      const res = await fetch(
        `/api/v1/firms/hotspots?country=${firmsCountry}&days=${firmsDays}`
      )
      const data = await res.json()
      setHotspots(data.hotspots || [])
    } catch (e) { console.error('FIRMS error:', e) }
    finally { setFirmsLoading(false) }
  }, [firmsCountry, firmsDays])

  useEffect(() => {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const latlng = { lat: pos.coords.latitude, lng: pos.coords.longitude }
        setLocation(latlng)
        setMapCenter([latlng.lat, latlng.lng])
        fetchData(latlng.lat, latlng.lng)
      },
      () => fetchData(48.5, 31.2)
    )
  }, [fetchData])

  useEffect(() => { fetchFIRMS() }, [fetchFIRMS])

  const DANGER_COUNTS = ['critical','high','medium','low'].reduce((acc, l) => {
    acc[l] = reports.filter(r => r.danger_level === l).length; return acc
  }, {})

  const FIRMS_COUNTRIES = ['Ukraine','Gaza','Sudan','Syria','Yemen','Iran','Iraq','Lebanon','Myanmar','Somalia','Ethiopia']

  return (
    <div style={{ height: 'calc(100vh - 56px)', display: 'flex', flexDirection: 'column' }}>

      {/* Toolbar */}
      <div style={{
        background: 'var(--bg2)', borderBottom: '1px solid var(--border)',
        padding: '8px 12px', display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
      }}>
        <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text2)' }}>
          {reports.length} REPORTS · {shelters.length} SHELTERS
        </span>
        {hotspots.length > 0 && (
          <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: '#ff6600' }}>
            · 🛰 {hotspots.length} FIRMS
          </span>
        )}
        <span style={{ fontSize: 10, color: 'var(--text2)', marginLeft: 4 }}>· CLICK MAP TO REPORT</span>

        <div style={{ display: 'flex', gap: 6, marginLeft: 'auto', alignItems: 'center', flexWrap: 'wrap' }}>
          {/* Danger counts */}
          {Object.entries(DANGER_COUNTS).map(([level, count]) => count > 0 && (
            <span key={level} style={{
              fontSize: 10, fontFamily: 'var(--mono)', padding: '2px 6px', borderRadius: 2,
              background: 'var(--bg3)', color: DANGER_COLORS[level] || 'var(--text2)',
            }}>{level.toUpperCase()}: {count}</span>
          ))}

          {/* Layer toggles */}
          <div style={{ display: 'flex', gap: 4, borderLeft: '1px solid var(--border)', paddingLeft: 8 }}>
            <button onClick={() => setShowReports(v => !v)} title="Toggle Reports" style={{
              background: showReports ? 'var(--red)' : 'var(--bg3)',
              color: showReports ? '#fff' : 'var(--text2)',
              padding: '3px 7px', borderRadius: 3, fontSize: 10, fontFamily: 'var(--mono)',
              border: '1px solid var(--border)',
            }}>RPT</button>
            <button onClick={() => setShowShelters(v => !v)} title="Toggle Shelters" style={{
              background: showShelters ? '#00cc66' : 'var(--bg3)',
              color: showShelters ? '#000' : 'var(--text2)',
              padding: '3px 7px', borderRadius: 3, fontSize: 10, fontFamily: 'var(--mono)',
              border: '1px solid var(--border)',
            }}>SHL</button>
            <button onClick={() => setShowFIRMS(v => !v)} title="Toggle FIRMS Hotspots" style={{
              background: showFIRMS ? '#ff6600' : 'var(--bg3)',
              color: showFIRMS ? '#fff' : 'var(--text2)',
              padding: '3px 7px', borderRadius: 3, fontSize: 10, fontFamily: 'var(--mono)',
              border: '1px solid var(--border)',
              display: 'flex', alignItems: 'center', gap: 3,
            }}>
              <Flame size={10} /> SAT
            </button>
          </div>

          {/* FIRMS controls — só visíveis quando SAT activo */}
          {showFIRMS && (
            <div style={{ display: 'flex', gap: 4, alignItems: 'center', borderLeft: '1px solid var(--border)', paddingLeft: 8 }}>
              <select value={firmsCountry} onChange={e => setFirmsCountry(e.target.value)}
                style={{ width: 'auto', padding: '4px 6px', fontSize: 10, fontFamily: 'var(--mono)' }}>
                {FIRMS_COUNTRIES.map(c => <option key={c} value={c}>{c.toUpperCase()}</option>)}
              </select>
              <select value={firmsDays} onChange={e => setFirmsDays(Number(e.target.value))}
                style={{ width: 'auto', padding: '4px 6px', fontSize: 10, fontFamily: 'var(--mono)' }}>
                {[1,2,3,5,7].map(d => <option key={d} value={d}>{d}d</option>)}
              </select>
              <button onClick={fetchFIRMS} disabled={firmsLoading} style={{
                background: 'var(--bg3)', color: firmsLoading ? '#ff6600' : 'var(--text)',
                padding: '4px 8px', border: '1px solid var(--border)', borderRadius: 3,
                display: 'flex', alignItems: 'center', gap: 4, fontSize: 10,
              }}>
                <RefreshCw size={10} style={{ animation: firmsLoading ? 'spin 1s linear infinite' : 'none' }} />
              </button>
            </div>
          )}

          {/* Radius + Refresh */}
          <div style={{ display: 'flex', gap: 4, borderLeft: '1px solid var(--border)', paddingLeft: 8 }}>
            <select value={radius} onChange={e => setRadius(Number(e.target.value))}
              style={{ width: 'auto', padding: '4px 6px', fontSize: 10, fontFamily: 'var(--mono)' }}>
              {[10,25,50,100].map(r => <option key={r} value={r}>{r}km</option>)}
            </select>
            <button onClick={() => location && fetchData(location.lat, location.lng)} style={{
              background: 'var(--bg3)', color: 'var(--text)', padding: '4px 10px',
              border: '1px solid var(--border)', borderRadius: 3,
              display: 'flex', alignItems: 'center', gap: 4, fontSize: 10,
            }}>
              <RefreshCw size={11} /> REFRESH
            </button>
          </div>
        </div>
      </div>

      {/* Map */}
      <div style={{ flex: 1, position: 'relative' }}>
        <MapContainer center={mapCenter} zoom={7} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; CARTO'
          />
          <ClickHandler onMapClick={setClickedLatlng} />

          {/* FIRMS hotspots — satélite */}
          {showFIRMS && hotspots.map((h, i) => {
            const s = frpStyle(h.frp, h.brightness)
            return (
              <CircleMarker
                key={`firms-${i}`}
                center={[h.latitude, h.longitude]}
                radius={s.radius}
                pathOptions={{
                  color: s.color,
                  fillColor: s.color,
                  fillOpacity: s.opacity,
                  weight: 1,
                }}
              >
                <Popup>
                  <div style={{ color: '#000', minWidth: 180 }}>
                    <strong style={{ color: s.color }}>🛰 NASA FIRMS HOTSPOT</strong><br />
                    <span style={{ fontSize: 11 }}>
                      <b>Brightness:</b> {h.brightness.toFixed(1)} K<br />
                      <b>FRP:</b> {h.frp.toFixed(2)} MW<br />
                      <b>Confidence:</b> {h.confidence === 'h' ? '🟢 High' : h.confidence === 'n' ? '🟡 Nominal' : '🔴 Low'}<br />
                      <b>Satellite:</b> {h.satellite} (VIIRS)<br />
                      <b>Time:</b> {h.datetime}<br />
                      <b>Day/Night:</b> {h.daynight === 'D' ? '☀️ Day' : '🌙 Night'}
                    </span>
                  </div>
                </Popup>
              </CircleMarker>
            )
          })}

          {/* Reports */}
          {showReports && reports.map(r => (
            <CircleMarker key={r.id} center={[r.lat, r.lng]} radius={8}
              pathOptions={{ color: DANGER_COLORS[r.danger_level] || '#888', fillColor: DANGER_COLORS[r.danger_level] || '#888', fillOpacity: 0.7, weight: 2 }}>
              <Popup>
                <div style={{ color: '#000', minWidth: 160 }}>
                  <strong>{r.report_type?.replace(/_/g,' ').toUpperCase()}</strong><br />
                  <span style={{ color: DANGER_COLORS[r.danger_level] }}>⚠ {r.danger_level?.toUpperCase()}</span>
                  {r.title && <p style={{ marginTop: 4, fontWeight: 600 }}>{r.title}</p>}
                  {r.description && <p style={{ marginTop: 2, fontSize: 12 }}>{r.description}</p>}
                </div>
              </Popup>
            </CircleMarker>
          ))}

          {/* Shelters */}
          {showShelters && shelters.map(s => (
            <CircleMarker key={s.id} center={[s.lat, s.lng]} radius={10}
              pathOptions={{ color: '#00cc66', fillColor: '#00cc66', fillOpacity: 0.8, weight: 2 }}>
              <Popup>
                <div style={{ color: '#000', minWidth: 160 }}>
                  <strong>🏠 {s.name}</strong><br />
                  <span>{s.shelter_type} — {s.status}</span>
                  {s.capacity_total && <p>Capacity: {s.capacity_current ?? '?'}/{s.capacity_total}</p>}
                  {s.operating_org && <p>Org: {s.operating_org}</p>}
                </div>
              </Popup>
            </CircleMarker>
          ))}
        </MapContainer>

        {/* Legenda FIRMS */}
        {showFIRMS && hotspots.length > 0 && (
          <div style={{
            position: 'absolute', bottom: 28, left: 12, zIndex: 1000,
            background: 'rgba(10,10,10,0.85)', border: '1px solid var(--border)',
            borderRadius: 6, padding: '8px 12px', fontFamily: 'var(--mono)', fontSize: 10,
          }}>
            <div style={{ color: '#ff6600', marginBottom: 6, letterSpacing: 1 }}>
              🛰 NASA FIRMS · {hotspots.length} DETECTIONS
            </div>
            {[
              { color: '#ff2b2b', label: 'EXTREME  FRP>50MW / >400K' },
              { color: '#ff6600', label: 'HIGH     FRP>20MW / >360K' },
              { color: '#ffb800', label: 'MODERATE FRP>5MW  / >330K' },
              { color: '#ff8c00', label: 'LOW      FRP≤5MW'          },
            ].map(({ color, label }) => (
              <div key={label} style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 3 }}>
                <div style={{ width: 10, height: 10, borderRadius: '50%', background: color, flexShrink: 0 }} />
                <span style={{ color: 'var(--text2)' }}>{label}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Report modal */}
      {clickedLatlng && (
        <ReportModal
          latlng={clickedLatlng}
          onClose={() => setClickedLatlng(null)}
          onSubmit={() => {
            setClickedLatlng(null)
            if (location) fetchData(location.lat, location.lng)
            else fetchData(48.5, 31.2)
          }}
        />
      )}

      <style>{`
        @keyframes spin { from { transform: rotate(0deg) } to { transform: rotate(360deg) } }
      `}</style>
    </div>
  )
}