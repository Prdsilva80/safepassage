import { useState, useEffect } from 'react'
import { Phone, Globe, MapPin, Shield, AlertTriangle, MessageSquare } from 'lucide-react'
import api from '../services/api'

const TYPE_LABEL = {
  switchboard: 'Switchboard',
  office: 'Local Office',
  hotline: 'Hotline',
  field: 'Field Office',
  form: 'Contact Form',
}

const TYPE_COLOR = {
  switchboard: 'var(--blue)',
  office: 'var(--green)',
  hotline: 'var(--red)',
  field: 'var(--yellow)',
  form: 'var(--text2)',
}

function Badge({ label, color, icon }) {
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 4,
      fontSize: 10, fontFamily: 'var(--mono)', letterSpacing: 1,
      padding: '2px 8px', borderRadius: 2,
      background: 'var(--bg3)', color, border: `1px solid ${color}44`,
    }}>
      {icon} {label}
    </span>
  )
}

function ContactCard({ contact }) {
  return (
    <div style={{
      background: 'var(--bg2)', border: '1px solid var(--border)',
      borderRadius: 6, padding: 20,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
        <div>
          <h3 style={{ fontFamily: 'var(--mono)', fontSize: 13, marginBottom: 4 }}>
            {contact.acronym && <span style={{ color: 'var(--red)', marginRight: 8 }}>{contact.acronym}</span>}
            {contact.organisation}
          </h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, color: 'var(--text2)', fontSize: 12 }}>
            <MapPin size={12} />
            {[contact.city, contact.country, contact.region].filter(Boolean).join(' · ')}
          </div>
        </div>
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
          <Badge label="OFFICIAL" color="var(--green)" icon={<Shield size={10} />} />
          <Badge
            label={TYPE_LABEL[contact.contact_type] || contact.contact_type}
            color={TYPE_COLOR[contact.contact_type] || 'var(--text2)'}
          />
          {contact.sms_confirmed
            ? <Badge label="SMS CONFIRMED" color="var(--green)" icon={<MessageSquare size={10} />} />
            : <Badge label="SMS UNVERIFIED" color="var(--yellow)" icon={<MessageSquare size={10} />} />
          }
        </div>
      </div>

      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 12 }}>
        {contact.phone && (
          <a href={`tel:${contact.phone}`} style={{
            display: 'flex', alignItems: 'center', gap: 6,
            color: 'var(--text)', fontSize: 13, fontFamily: 'var(--mono)',
          }}>
            <Phone size={14} color="var(--green)" /> {contact.phone}
          </a>
        )}
        {contact.website && (
          <a href={contact.website} target="_blank" rel="noopener noreferrer" style={{
            display: 'flex', alignItems: 'center', gap: 6,
            color: 'var(--blue)', fontSize: 12,
          }}>
            <Globe size={14} /> {contact.website.replace('https://', '')}
          </a>
        )}
      </div>

      {contact.notes && (
        <div style={{
          background: 'var(--bg3)', border: '1px solid var(--border)',
          borderRadius: 4, padding: '8px 12px',
          display: 'flex', gap: 8, alignItems: 'flex-start',
        }}>
          <AlertTriangle size={13} color="var(--yellow)" style={{ marginTop: 2, flexShrink: 0 }} />
          <p style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.6 }}>{contact.notes}</p>
        </div>
      )}

      {contact.source_url && (
        <div style={{ marginTop: 8 }}>
          <a href={contact.source_url} target="_blank" rel="noopener noreferrer"
            style={{ fontSize: 11, color: 'var(--text2)', fontFamily: 'var(--mono)' }}>
            SOURCE: {contact.source_url}
          </a>
          {contact.last_verified_at && (
            <span style={{ fontSize: 11, color: 'var(--text2)', marginLeft: 12 }}>
              VERIFIED: {new Date(contact.last_verified_at).toLocaleDateString()}
            </span>
          )}
        </div>
      )}
    </div>
  )
}

export default function ContactsPage() {
  const [contacts, setContacts] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('')

  useEffect(() => {
    api.get('/contacts/')
      .then(r => setContacts(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const filtered = contacts.filter(c =>
    !filter ||
    c.organisation.toLowerCase().includes(filter.toLowerCase()) ||
    c.country?.toLowerCase().includes(filter.toLowerCase()) ||
    c.acronym?.toLowerCase().includes(filter.toLowerCase())
  )

  return (
    <div style={{ padding: 24, maxWidth: 900, margin: '0 auto' }}>
      <p style={{ fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: 3, color: 'var(--text2)', marginBottom: 8 }}>
        EMERGENCY CONTACTS
      </p>

      <div style={{
        background: 'var(--bg3)', border: '1px solid var(--yellow)',
        borderRadius: 4, padding: '10px 14px', marginBottom: 24,
        display: 'flex', gap: 8, alignItems: 'flex-start',
      }}>
        <AlertTriangle size={14} color="var(--yellow)" style={{ marginTop: 2, flexShrink: 0 }} />
        <p style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.7 }}>
          These are official public organisational contacts. Availability for SMS, WhatsApp, emergency response
          or local field assistance may vary by country and operation.
          <strong style={{ color: 'var(--text)' }}> Always verify contact details before relying on them in an emergency.</strong>
        </p>
      </div>

      <div style={{ marginBottom: 20 }}>
        <input
          placeholder="Search by organisation, country or acronym..."
          value={filter}
          onChange={e => setFilter(e.target.value)}
          style={{ maxWidth: 400 }}
        />
      </div>

      {loading ? (
        <p style={{ color: 'var(--text2)', fontFamily: 'var(--mono)' }}>LOADING...</p>
      ) : filtered.length === 0 ? (
        <p style={{ color: 'var(--text2)' }}>No contacts found.</p>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          {filtered.map(c => <ContactCard key={c.id} contact={c} />)}
        </div>
      )}

      <p style={{ fontSize: 11, color: 'var(--text2)', fontFamily: 'var(--mono)', marginTop: 32, textAlign: 'center' }}>
        {contacts.length} CONTACTS · LAST UPDATED: {new Date().toLocaleDateString()}
      </p>
    </div>
  )
}
