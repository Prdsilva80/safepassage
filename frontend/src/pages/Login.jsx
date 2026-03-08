import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { useTranslation } from 'react-i18next'
import { Shield, AlertTriangle } from 'lucide-react'
import LanguageSelector from '../components/LanguageSelector'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, loginAnonymous } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      await login(username, password)
      navigate('/map')
    } catch {
      setError(t('login.invalid_credentials'))
    } finally { setLoading(false) }
  }

  const handleAnon = async () => {
    setLoading(true)
    try {
      await loginAnonymous()
      navigate('/civil')
    } catch { setError(t('login.anon_failed')) }
    finally { setLoading(false) }
  }

  return (
    <div style={{
      minHeight: '100vh', background: 'var(--bg)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
    }}>
      <div style={{ width: 360 }}>
        <div style={{ textAlign: 'center', marginBottom: 40 }}>
          <Shield size={48} color="var(--red)" />
          <h1 style={{ fontFamily: 'var(--mono)', fontSize: 24, letterSpacing: 4, marginTop: 12, color: 'var(--red)' }}>
            {t('login.title')}
          </h1>
          <p style={{ color: 'var(--text2)', marginTop: 8, fontSize: 12, letterSpacing: 2 }}>
            {t('login.subtitle')}
          </p>
          <div style={{ marginTop: 12, display: 'flex', justifyContent: 'center' }}>
            <LanguageSelector />
          </div>
        </div>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            placeholder={t('login.username')}
            value={username}
            onChange={e => setUsername(e.target.value)}
            style={{ fontFamily: 'var(--mono)', letterSpacing: 1 }}
          />
          <input
            type="password"
            placeholder={t('login.password')}
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={{ fontFamily: 'var(--mono)', letterSpacing: 1 }}
          />

          <p style={{ textAlign: 'center', fontSize: 12, marginTop: -4 }}>
            {t('login.no_account')}{' '}
            <a href="/register" style={{ color: 'var(--red)' }}>{t('login.register')}</a>
          </p>

          {error && (
            <div style={{ color: 'var(--red)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertTriangle size={14} /> {error}
            </div>
          )}

          <button type="submit" disabled={loading} style={{
            background: 'var(--red)', color: '#fff', padding: '12px',
            fontFamily: 'var(--mono)', letterSpacing: 2, fontSize: 13,
            borderRadius: 4, marginTop: 8, opacity: loading ? 0.7 : 1,
          }}>
            {loading ? t('login.connecting') : t('login.login')}
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '20px 0' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span style={{ color: 'var(--text2)', fontSize: 11, fontFamily: 'var(--mono)' }}>{t('login.or')}</span>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>

        <button onClick={handleAnon} disabled={loading} style={{
          width: '100%', background: 'var(--bg3)', color: 'var(--text2)',
          padding: '12px', fontFamily: 'var(--mono)', letterSpacing: 2,
          fontSize: 12, borderRadius: 4, border: '1px solid var(--border)',
        }}>
          {t('login.anonymous')}
        </button>

        <p style={{ color: 'var(--text2)', fontSize: 11, textAlign: 'center', marginTop: 24, lineHeight: 1.8 }}>
          {t('login.anonymous_desc')}
        </p>
      </div>
    </div>
  )
}
