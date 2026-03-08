import { useState } from 'react'
import { sosAPI, aiAPI } from '../../services/api'
import { useTranslation } from 'react-i18next'
import { AlertTriangle, Shield, MapPin, Users, Heart, Loader } from 'lucide-react'

const S = {
  page: { padding: 24, maxWidth: 800, margin: '0 auto' },
  title: { fontFamily: 'var(--mono)', fontSize: 11, letterSpacing: 3, color: 'var(--text2)', marginBottom: 16 },
  card: { background: 'var(--bg2)', border: '1px solid var(--border)', borderRadius: 6, padding: 20, marginBottom: 16 },
  h2: { fontFamily: 'var(--mono)', fontSize: 16, marginBottom: 16 },
  btn: (color='var(--red)') => ({
    background: color, color: '#fff', padding: '10px 20px',
    borderRadius: 4, fontFamily: 'var(--mono)', letterSpacing: 1,
    fontSize: 12, display: 'flex', alignItems: 'center', gap: 8,
  }),
  row: { display: 'flex', gap: 12, flexWrap: 'wrap' },
  field: { display: 'flex', flexDirection: 'column', gap: 6, flex: 1, minWidth: 140 },
  label: { fontSize: 11, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1 },
}

export default function CivilPage() {
  const { t, i18n } = useTranslation()
  const [sosForm, setSosForm] = useState({ lat: '', lng: '', message: '', people_count: 1, has_injured: false, has_children: false })
  const [sosSent, setSosSent] = useState(false)
  const [sosLoading, setSosLoading] = useState(false)

  const [aiForm, setAiForm] = useState({ lat: '', lng: '', has_vehicle: false, needs_medical_attention: false, group_size: 1, language: i18n.language })
  const [aiResult, setAiResult] = useState(null)
  const [aiLoading, setAiLoading] = useState(false)

  const getLocation = (setter) => {
    navigator.geolocation.getCurrentPosition(
      (pos) => setter(f => ({ ...f, lat: pos.coords.latitude.toFixed(5), lng: pos.coords.longitude.toFixed(5) })),
      () => alert('Could not get location')
    )
  }

  const sendSOS = async () => {
    setSosLoading(true)
    try {
      await sosAPI.trigger({ ...sosForm, lat: parseFloat(sosForm.lat), lng: parseFloat(sosForm.lng), people_count: parseInt(sosForm.people_count) })
      setSosSent(true)
    } catch (e) { alert('SOS failed: ' + (e.response?.data?.detail || e.message)) }
    finally { setSosLoading(false) }
  }

  const getAI = async () => {
    setAiLoading(true)
    try {
      const res = await aiAPI.assess({ ...aiForm, lat: parseFloat(aiForm.lat), lng: parseFloat(aiForm.lng), group_size: parseInt(aiForm.group_size), language: i18n.language })
      setAiResult(res.data)
    } catch (e) { alert('AI failed: ' + (e.response?.data?.detail || e.message)) }
    finally { setAiLoading(false) }
  }

  const RISK_COLOR = { low: 'var(--green)', medium: 'var(--yellow)', high: '#ff6600', critical: 'var(--red)' }

  return (
    <div style={S.page}>
      <p style={S.title}>{t('civil.title')}</p>

      <div style={{ ...S.card, borderColor: sosSent ? 'var(--green)' : 'var(--red)' }}>
        <h2 style={{ ...S.h2, color: 'var(--red)' }}>
          <AlertTriangle size={16} style={{ display: 'inline', marginRight: 8 }} />
          {t('civil.sos_title')}
        </h2>

        {sosSent ? (
          <div style={{ color: 'var(--green)', fontFamily: 'var(--mono)', fontSize: 13 }}>
            ✓ {t('civil.sos_sent')}
          </div>
        ) : (
          <>
            <div style={S.row}>
              <div style={S.field}>
                <label style={S.label}>{t('civil.latitude')}</label>
                <input value={sosForm.lat} onChange={e => setSosForm(f => ({...f, lat: e.target.value}))} placeholder="48.5000" />
              </div>
              <div style={S.field}>
                <label style={S.label}>{t('civil.longitude')}</label>
                <input value={sosForm.lng} onChange={e => setSosForm(f => ({...f, lng: e.target.value}))} placeholder="31.2000" />
              </div>
              <div style={{ display: 'flex', alignItems: 'flex-end' }}>
                <button onClick={() => getLocation(setSosForm)} style={{ ...S.btn('var(--bg3)'), color: 'var(--text)', border: '1px solid var(--border)' }}>
                  <MapPin size={14} /> {t('civil.gps')}
                </button>
              </div>
            </div>

            <div style={{ ...S.row, marginTop: 12 }}>
              <div style={S.field}>
                <label style={S.label}>{t('civil.people_count')}</label>
                <input type="number" min="1" value={sosForm.people_count} onChange={e => setSosForm(f => ({...f, people_count: e.target.value}))} />
              </div>
              <div style={S.field}>
                <label style={S.label}>{t('civil.message')}</label>
                <input value={sosForm.message} onChange={e => setSosForm(f => ({...f, message: e.target.value}))} placeholder={t('civil.message_placeholder')} />
              </div>
            </div>

            <div style={{ display: 'flex', gap: 16, margin: '12px 0' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, cursor: 'pointer' }}>
                <input type="checkbox" checked={sosForm.has_injured} onChange={e => setSosForm(f => ({...f, has_injured: e.target.checked}))} style={{ width: 'auto' }} />
                <Heart size={13} color="var(--red)" /> {t('civil.injured')}
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, cursor: 'pointer' }}>
                <input type="checkbox" checked={sosForm.has_children} onChange={e => setSosForm(f => ({...f, has_children: e.target.checked}))} style={{ width: 'auto' }} />
                <Users size={13} color="var(--yellow)" /> {t('civil.children')}
              </label>
            </div>

            <button onClick={sendSOS} disabled={!sosForm.lat || !sosForm.lng || sosLoading} style={S.btn()}>
              {sosLoading ? <Loader size={14} /> : <AlertTriangle size={14} />}
              {sosLoading ? t('civil.sending') : t('civil.send_sos')}
            </button>
          </>
        )}
      </div>

      <div style={S.card}>
        <h2 style={{ ...S.h2, color: 'var(--blue)' }}>
          <Shield size={16} style={{ display: 'inline', marginRight: 8 }} />
          {t('civil.ai_title')}
        </h2>

        <div style={S.row}>
          <div style={S.field}>
            <label style={S.label}>{t('civil.latitude')}</label>
            <input value={aiForm.lat} onChange={e => setAiForm(f => ({...f, lat: e.target.value}))} placeholder="48.5000" />
          </div>
          <div style={S.field}>
            <label style={S.label}>{t('civil.longitude')}</label>
            <input value={aiForm.lng} onChange={e => setAiForm(f => ({...f, lng: e.target.value}))} placeholder="31.2000" />
          </div>
          <div style={{ display: 'flex', alignItems: 'flex-end' }}>
            <button onClick={() => getLocation(setAiForm)} style={{ ...S.btn('var(--bg3)'), color: 'var(--text)', border: '1px solid var(--border)' }}>
              <MapPin size={14} /> {t('civil.gps')}
            </button>
          </div>
        </div>

        <div style={{ display: 'flex', gap: 16, margin: '12px 0', flexWrap: 'wrap' }}>
          {[
            ['has_vehicle', t('civil.has_vehicle')],
            ['needs_medical_attention', t('civil.needs_medical')],
            ['has_children', t('civil.has_children')],
          ].map(([key, label]) => (
            <label key={key} style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, cursor: 'pointer' }}>
              <input type="checkbox" checked={aiForm[key] || false} onChange={e => setAiForm(f => ({...f, [key]: e.target.checked}))} style={{ width: 'auto' }} />
              {label}
            </label>
          ))}
        </div>

        <button onClick={getAI} disabled={!aiForm.lat || !aiForm.lng || aiLoading} style={S.btn('var(--blue)')}>
          {aiLoading ? <Loader size={14} /> : <Shield size={14} />}
          {aiLoading ? t('civil.analysing') : t('civil.get_assessment')}
        </button>

        {aiResult && (
          <div style={{ marginTop: 20, borderTop: '1px solid var(--border)', paddingTop: 20 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 16 }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 20, fontWeight: 700, color: RISK_COLOR[aiResult.risk_level] || 'var(--text)' }}>
                {aiResult.risk_level?.toUpperCase()}
              </span>
              <span style={{ color: 'var(--text2)', fontSize: 12 }}>
                Score: {(aiResult.risk_score * 100).toFixed(0)}% · Confidence: {(aiResult.ai_confidence * 100).toFixed(0)}%
              </span>
            </div>
            <p style={{ marginBottom: 16, lineHeight: 1.7 }}>{aiResult.summary}</p>
            <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text2)', marginBottom: 8 }}>{t('civil.immediate_actions')}</p>
            <ul style={{ paddingLeft: 16, display: 'flex', flexDirection: 'column', gap: 4 }}>
              {aiResult.immediate_actions?.map((a, i) => <li key={i} style={{ color: 'var(--yellow)', fontSize: 13 }}>{a}</li>)}
            </ul>
            {aiResult.evacuation_plan && (
              <>
                <p style={{ fontFamily: 'var(--mono)', fontSize: 11, color: 'var(--text2)', margin: '16px 0 8px' }}>{t('civil.evacuation_plan')}</p>
                <p style={{ whiteSpace: 'pre-line', lineHeight: 1.7, fontSize: 13 }}>{aiResult.evacuation_plan}</p>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
