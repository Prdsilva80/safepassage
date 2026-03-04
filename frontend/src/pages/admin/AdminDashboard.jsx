import { useState, useEffect } from 'react'
import { zonesAPI, reportsAPI, sheltersAPI, sosAPI } from '../../services/api'
import { AlertTriangle, MapPin, Home, Activity } from 'lucide-react'

function StatCard({ label, value, color, icon }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: `1px solid ${color}33`,
      borderRadius: 6, padding: 20, flex: 1, minWidth: 140,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--text2)', letterSpacing: 2 }}>{label}</p>
          <p style={{ fontFamily: 'var(--mono)', fontSize: 32, color, marginTop: 8 }}>{value}</p>
        </div>
        <div style={{ color, opacity: 0.5 }}>{icon}</div>
      </div>
    </div>
  )
}

export default function AdminDashboard() {
  const [zones, setZones] = useState([])
  const [sosList, setSosList] = useState([])
  const [loading, setLoading] = useState(true)
  const [newZone, setNewZone] = useState({ name: '', country: '', center_lat: '', center_lng: '', radius_km: 50 })
  const [creating, setCreating] = useState(false)

  useEffect(() => {
    Promise.all([zonesAPI.list(), sosAPI.active()])
      .then(([z, s]) => { setZones(z.data); setSosList(s.data) })
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const createZone = async () => {
    setCreating(true)
    try {
      const res = await zonesAPI.create({
        ...newZone,
        center_lat: parseFloat(newZone.center_lat),
        center_lng: parseFloat(newZone.center_lng),
        radius_km: parseFloat(newZone.radius_km),
      })
      setZones(z => [...z, res.data])
      setNewZone({ name: '', country: '', center_lat: '', center_lng: '', radius_km: 50 })
    } catch (e) { alert(e.response?.data?.detail || e.message) }
    finally { setCreating(false) }
  }

  const acknowledgeSOSItem = async (id) => {
    try {
      await sosAPI.acknowledge(id, 'Admin')
      setSosList(s => s.map(x => x.id === id ? { ...x, status: 'acknowledged' } : x))
    } catch (e) { alert(e.message) }
  }

  if (loading) return <div style={{ padding: 24, color: 'var(--text2)', fontFamily: 'var(--mono)' }}>LOADING...</div>

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: '0 auto' }}>
      <p style={{ fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: 3, color: 'var(--text2)', marginBottom: 24 }}>
        ADMIN DASHBOARD
      </p>

      <div style={{ display: 'flex', gap: 16, marginBottom: 32, flexWrap: 'wrap' }}>
        <StatCard label="ACTIVE ZONES" value={zones.length} color="var(--blue)" icon={<MapPin size={24} />} />
        <StatCard label="ACTIVE SOS" value={sosList.filter(s => s.status === 'active').length} color="var(--red)" icon={<AlertTriangle size={24} />} />
        <StatCard label="TOTAL SOS" value={sosList.length} color="var(--yellow)" icon={<Activity size={24} />} />
      </div>

      {/* Active SOS */}
      {sosList.filter(s => s.status === 'active').length > 0 && (
        <div style={{ background: 'var(--bg2)', border: '1px solid var(--red)', borderRadius: 6, padding: 20, marginBottom: 24 }}>
          <h2 style={{ fontFamily: 'var(--mono)', fontSize: 13, color: 'var(--red)', marginBottom: 16, letterSpacing: 2 }}>
            ⚠ ACTIVE SOS EVENTS
          </h2>
          {sosList.filter(s => s.status === 'active').map(sos => (
            <div key={sos.id} style={{
              background: 'var(--bg3)', border: '1px solid var(--border)',
              borderRadius: 4, padding: 12, marginBottom: 8,
              display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8,
            }}>
              <div>
                <span style={{ fontFamily: 'var(--mono)', fontSize: 12, color: 'var(--red)' }}>
                  📍 {sos.lat?.toFixed(4)}, {sos.lng?.toFixed(4)}
                </span>
                <span style={{ marginLeft: 12, color: 'var(--text2)', fontSize: 12 }}>
                  👥 {sos.people_count} people
                  {sos.has_injured && ' · 🩹 INJURED'}
                  {sos.has_children && ' · 👶 CHILDREN'}
                </span>
                {sos.message && <p style={{ color: 'var(--text)', fontSize: 12, marginTop: 4 }}>{sos.message}</p>}
              </div>
              <button onClick={() => acknowledgeSOSItem(sos.id)} style={{
                background: 'var(--yellow)', color: '#000', padding: '6px 14px',
                borderRadius: 3, fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: 1,
              }}>
                ACKNOWLEDGE
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Create Zone */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: 20, marginBottom: 24 }}>
        <h2 style={{ fontFamily: 'var(--mono)', fontSize: 13, letterSpacing: 2, marginBottom: 16, color: 'var(--text2)' }}>
          CREATE CONFLICT ZONE
        </h2>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          {[['name','ZONE NAME','text'],['country','COUNTRY','text'],['center_lat','CENTER LAT','text'],['center_lng','CENTER LNG','text'],['radius_km','RADIUS KM','number']].map(([key, label]) => (
            <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 120 }}>
              <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1 }}>{label}</label>
              <input value={newZone[key]} onChange={e => setNewZone(z => ({...z, [key]: e.target.value}))} />
            </div>
          ))}
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button onClick={createZone} disabled={creating || !newZone.name} style={{
              background: 'var(--blue)', color: '#fff', padding: '8px 16px',
              borderRadius: 4, fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: 1,
            }}>
              {creating ? 'CREATING...' : '+ CREATE'}
            </button>
          </div>
        </div>
      </div>

      {/* Zones list */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: 20 }}>
        <h2 style={{ fontFamily: 'var(--mono)', fontSize: 13, letterSpacing: 2, marginBottom: 16, color: 'var(--text2)' }}>
          CONFLICT ZONES ({zones.length})
        </h2>
        {zones.length === 0 ? (
          <p style={{ color: 'var(--text2)', fontSize: 12 }}>No zones registered yet.</p>
        ) : zones.map(zone => (
          <div key={zone.id} style={{
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            padding: '10px 0', borderBottom: '1px solid var(--border)', flexWrap: 'wrap', gap: 8,
          }}>
            <div>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{zone.name}</span>
              <span style={{ color: 'var(--text2)', fontSize: 12, marginLeft: 12 }}>{zone.country}</span>
            </div>
            <span style={{
              fontFamily: 'var(--mono)', fontSize: 11, padding: '2px 8px', borderRadius: 2,
              background: 'var(--bg3)',
              color: zone.danger_level === 'critical' ? 'var(--red)' : zone.danger_level === 'high' ? '#ff6600' : 'var(--yellow)',
            }}>
              {zone.danger_level?.toUpperCase()}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
