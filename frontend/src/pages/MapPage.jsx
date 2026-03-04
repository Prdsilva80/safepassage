import { useState, useEffect, useCallback } from 'react'
import { MapContainer, TileLayer, CircleMarker, Popup, useMapEvents } from 'react-leaflet'
import 'leaflet/dist/leaflet.css'
import { reportsAPI, sheltersAPI } from '../services/api'
import { RefreshCw, X, AlertTriangle } from 'lucide-react'

const DANGER_COLORS = {
  critical: '#ff2b2b', high: '#ff6600', medium: '#ffb800', low: '#00cc66', safe: '#0088ff',
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
  const [reports, setReports] = useState([])
  const [shelters, setShelters] = useState([])
  const [location, setLocation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [radius, setRadius] = useState(50)
  const [clickedLatlng, setClickedLatlng] = useState(null)
  const [mapCenter, setMapCenter] = useState([48.5, 31.2])

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
  }, [])

  const DANGER_COUNTS = ['critical','high','medium','low'].reduce((acc, l) => {
    acc[l] = reports.filter(r => r.danger_level === l).length; return acc
  }, {})

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
        <span style={{ fontSize: 10, color: 'var(--text2)', marginLeft: 4 }}>· CLICK MAP TO REPORT</span>

        <div style={{ display: 'flex', gap: 6, marginLeft: 'auto', alignItems: 'center', flexWrap: 'wrap' }}>
          {Object.entries(DANGER_COUNTS).map(([level, count]) => count > 0 && (
            <span key={level} style={{
              fontSize: 10, fontFamily: 'var(--mono)', padding: '2px 6px', borderRadius: 2,
              background: 'var(--bg3)',
              color: DANGER_COLORS[level] || 'var(--text2)',
            }}>{level.toUpperCase()}: {count}</span>
          ))}
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

      {/* Map */}
      <div style={{ flex: 1 }}>
        <MapContainer center={mapCenter} zoom={7} style={{ height: '100%', width: '100%' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; CARTO'
          />
          <ClickHandler onMapClick={setClickedLatlng} />

          {reports.map(r => (
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

          {shelters.map(s => (
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
    </div>
  )
}
