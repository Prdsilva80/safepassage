import { useState, useEffect } from 'react'
import { sheltersAPI } from '../../services/api'
import { Plus, Edit2, Check } from 'lucide-react'

const FIELD = ({ label, value, onChange, type = 'text', options }) => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, flex: 1, minWidth: 120 }}>
    <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1 }}>{label}</label>
    {options
      ? <select value={value} onChange={e => onChange(e.target.value)}>
          {options.map(o => <option key={o} value={o}>{o.toUpperCase()}</option>)}
        </select>
      : <input type={type} value={value} onChange={e => onChange(e.target.value)} />
    }
  </div>
)

const empty = { name: '', lat: '', lng: '', shelter_type: 'building', status: 'active', capacity_total: '', operating_org: '', address: '' }

export default function SheltersAdmin() {
  const [shelters, setShelters] = useState([])
  const [form, setForm] = useState(empty)
  const [loading, setLoading] = useState(true)
  const [creating, setCreating] = useState(false)
  const [editId, setEditId] = useState(null)
  const [editData, setEditData] = useState({})

  useEffect(() => {
    sheltersAPI.nearby(48.5, 31.2, 5000)
      .then(r => setShelters(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const createShelter = async () => {
    setCreating(true)
    try {
      const res = await sheltersAPI.create({
        ...form, lat: parseFloat(form.lat), lng: parseFloat(form.lng),
        capacity_total: form.capacity_total ? parseInt(form.capacity_total) : null,
      })
      setShelters(s => [...s, res.data])
      setForm(empty)
    } catch (e) { alert(e.response?.data?.detail || e.message) }
    finally { setCreating(false) }
  }

  const saveEdit = async (id) => {
    try {
      const res = await sheltersAPI.update(id, editData)
      setShelters(s => s.map(x => x.id === id ? res.data : x))
      setEditId(null)
    } catch (e) { alert(e.response?.data?.detail || e.message) }
  }

  const STATUS_COLOR = { active: 'var(--green)', full: 'var(--yellow)', closed: 'var(--red)', unknown: 'var(--text2)' }

  return (
    <div style={{ padding: 24, maxWidth: 1100, margin: '0 auto' }}>
      <p style={{ fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: 3, color: 'var(--text2)', marginBottom: 24 }}>
        SHELTER MANAGEMENT
      </p>

      {/* Create form */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: 20, marginBottom: 24 }}>
        <h2 style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: 2, marginBottom: 16, color: 'var(--text2)' }}>
          <Plus size={14} style={{ display: 'inline', marginRight: 6 }} />ADD SHELTER
        </h2>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 10 }}>
          <FIELD label="NAME" value={form.name} onChange={v => setForm(f => ({...f, name: v}))} />
          <FIELD label="LATITUDE" value={form.lat} onChange={v => setForm(f => ({...f, lat: v}))} />
          <FIELD label="LONGITUDE" value={form.lng} onChange={v => setForm(f => ({...f, lng: v}))} />
          <FIELD label="CAPACITY" type="number" value={form.capacity_total} onChange={v => setForm(f => ({...f, capacity_total: v}))} />
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 16 }}>
          <FIELD label="TYPE" value={form.shelter_type} onChange={v => setForm(f => ({...f, shelter_type: v}))}
            options={['building','camp','hospital','school','community_center','underground','other']} />
          <FIELD label="STATUS" value={form.status} onChange={v => setForm(f => ({...f, status: v}))}
            options={['active','full','closed','unknown']} />
          <FIELD label="ORGANISATION" value={form.operating_org} onChange={v => setForm(f => ({...f, operating_org: v}))} />
          <FIELD label="ADDRESS" value={form.address} onChange={v => setForm(f => ({...f, address: v}))} />
        </div>
        <button onClick={createShelter} disabled={creating || !form.name || !form.lat || !form.lng} style={{
          background: 'var(--green)', color: '#000', padding: '8px 20px',
          borderRadius: 4, fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: 1,
          opacity: creating || !form.name ? 0.5 : 1,
        }}>
          {creating ? 'CREATING...' : '+ CREATE SHELTER'}
        </button>
      </div>

      {/* Shelters list */}
      <div style={{ background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: 20 }}>
        <h2 style={{ fontFamily: 'var(--mono)', fontSize: 12, letterSpacing: 2, marginBottom: 16, color: 'var(--text2)' }}>
          SHELTERS ({shelters.length})
        </h2>

        {loading ? <p style={{ color: 'var(--text2)' }}>Loading...</p> :
         shelters.length === 0 ? <p style={{ color: 'var(--text2)', fontSize: 12 }}>No shelters registered.</p> :
         shelters.map(s => (
          <div key={s.id} style={{
            padding: '12px 0', borderBottom: '1px solid var(--border)',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8,
          }}>
            {editId === s.id ? (
              <div style={{ display: 'flex', gap: 8, flex: 1, flexWrap: 'wrap', alignItems: 'center' }}>
                <input value={editData.name || ''} onChange={e => setEditData(d => ({...d, name: e.target.value}))}
                  style={{ flex: 1, minWidth: 120 }} placeholder="Name" />
                <select value={editData.status || s.status} onChange={e => setEditData(d => ({...d, status: e.target.value}))}>
                  {['active','full','closed','unknown'].map(o => <option key={o} value={o}>{o.toUpperCase()}</option>)}
                </select>
                <input type="number" value={editData.capacity_current ?? ''} onChange={e => setEditData(d => ({...d, capacity_current: parseInt(e.target.value)}))}
                  style={{ width: 80 }} placeholder="Current" />
                <button onClick={() => saveEdit(s.id)} style={{
                  background: 'var(--green)', color: '#000', padding: '6px 12px',
                  borderRadius: 3, fontFamily: 'var(--mono)', fontSize: 11,
                }}><Check size={12} /></button>
              </div>
            ) : (
              <>
                <div>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 13 }}>{s.name}</span>
                  <span style={{ color: 'var(--text2)', fontSize: 12, marginLeft: 10 }}>{s.shelter_type}</span>
                  {s.operating_org && <span style={{ color: 'var(--text2)', fontSize: 11, marginLeft: 10 }}>· {s.operating_org}</span>}
                  <div style={{ fontSize: 11, color: 'var(--text2)', marginTop: 2 }}>
                    📍 {s.lat?.toFixed(4)}, {s.lng?.toFixed(4)}
                    {s.capacity_total && <span style={{ marginLeft: 8 }}>👥 {s.capacity_current ?? 0}/{s.capacity_total}</span>}
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{
                    fontFamily: 'var(--mono)', fontSize: 10, padding: '2px 8px',
                    borderRadius: 2, background: 'var(--bg3)',
                    color: STATUS_COLOR[s.status] || 'var(--text2)',
                  }}>{s.status?.toUpperCase()}</span>
                  <button onClick={() => { setEditId(s.id); setEditData({ name: s.name, status: s.status, capacity_current: s.capacity_current }) }}
                    style={{ background: 'var(--bg3)', color: 'var(--text2)', padding: '4px 8px', borderRadius: 3, border: '1px solid var(--border)' }}>
                    <Edit2 size={12} />
                  </button>
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
