import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Shield, AlertTriangle } from 'lucide-react'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const { login, loginAnonymous } = useAuth()
  const navigate = useNavigate()

  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      await login(username, password)
      navigate('/map')
    } catch {
      setError('Invalid credentials')
    } finally { setLoading(false) }
  }

  const handleAnon = async () => {
    setLoading(true)
    try {
      await loginAnonymous()
      navigate('/civil')
    } catch { setError('Failed to create anonymous session') }
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
            SAFEPASSAGE
          </h1>
          <p style={{ color: 'var(--text2)', marginTop: 8, fontSize: 12, letterSpacing: 2 }}>
            HUMANITARIAN SAFETY SYSTEM
          </p>
        </div>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <input
            placeholder="USERNAME"
            value={username}
            onChange={e => setUsername(e.target.value)}
            style={{ fontFamily: 'var(--mono)', letterSpacing: 1 }}
          />
          <input
            type="password"
            placeholder="PASSWORD"
            value={password}
            onChange={e => setPassword(e.target.value)}
            style={{ fontFamily: 'var(--mono)', letterSpacing: 1 }}
          />

          {error && (
            <div style={{ color: 'var(--red)', fontSize: 12, display: 'flex', alignItems: 'center', gap: 6 }}>
              <AlertTriangle size={14} /> {error}
            </div>
          )}

          <button type="submit" disabled={loading} style={{
            background: 'var(--red)', color: '#fff', padding: '12px',
            fontFamily: 'var(--mono)', letterSpacing: 2, fontSize: 13,
            borderRadius: 4, marginTop: 8,
            opacity: loading ? 0.7 : 1,
          }}>
            {loading ? 'CONNECTING...' : 'LOGIN'}
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, margin: '20px 0' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span style={{ color: 'var(--text2)', fontSize: 11, fontFamily: 'var(--mono)' }}>OR</span>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>

        <button onClick={handleAnon} disabled={loading} style={{
          width: '100%', background: 'var(--bg3)', color: 'var(--text2)',
          padding: '12px', fontFamily: 'var(--mono)', letterSpacing: 2,
          fontSize: 12, borderRadius: 4, border: '1px solid var(--border)',
        }}>
          ENTER AS ANONYMOUS CIVILIAN
        </button>

        <p style={{ color: 'var(--text2)', fontSize: 11, textAlign: 'center', marginTop: 24, lineHeight: 1.8 }}>
          Anonymous access provides immediate safety information<br />without registration required.
        </p>
      </div>
      <p style={{ color: 'var(--text2)', fontSize: 12, textAlign: 'center', marginTop: 16 }}>
        Don't have an account?{' '}
        <a href="/register" style={{ color: 'var(--red)' }}>REGISTER</a>
      </p>
    </div>
  )
}
