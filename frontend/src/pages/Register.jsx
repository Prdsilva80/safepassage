import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { authAPI } from '../services/api'
import { Shield, AlertTriangle, CheckCircle } from 'lucide-react'

export default function Register() {
  const [form, setForm] = useState({ username: '', email: '', password: '', display_name: '', role: 'civilian' })
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true); setError('')
    try {
      await authAPI.register(form)
      setSuccess(true)
      setTimeout(() => navigate('/login'), 2000)
    } catch (err) {
      setError(err.response?.data?.detail || 'Registration failed')
    } finally { setLoading(false) }
  }

  if (success) return (
    <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
      <div style={{ textAlign: 'center' }}>
        <CheckCircle size={48} color="var(--green)" />
        <h2 style={{ fontFamily: 'var(--mono)', marginTop: 16, color: 'var(--green)' }}>ACCOUNT CREATED</h2>
        <p style={{ color: 'var(--text2)', marginTop: 8 }}>Redirecting to login...</p>
      </div>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div style={{ width: '100%', maxWidth: 400 }}>
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Shield size={40} color="var(--red)" />
          <h1 style={{ fontFamily: 'var(--mono)', fontSize: 20, letterSpacing: 4, marginTop: 12, color: 'var(--red)' }}>REGISTER</h1>
          <p style={{ color: 'var(--text2)', fontSize: 12, letterSpacing: 2, marginTop: 4 }}>CREATE ACCOUNT</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[
            ['username', 'USERNAME', 'text'],
            ['display_name', 'DISPLAY NAME', 'text'],
            ['email', 'EMAIL', 'email'],
            ['password', 'PASSWORD', 'password'],
          ].map(([key, label, type]) => (
            <div key={key} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1 }}>{label}</label>
              <input
                type={type}
                value={form[key]}
                onChange={e => setForm(f => ({ ...f, [key]: e.target.value }))}
                required={key !== 'display_name'}
                style={{ fontFamily: 'var(--mono)' }}
              />
            </div>
          ))}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
            <label style={{ fontSize: 10, color: 'var(--text2)', fontFamily: 'var(--mono)', letterSpacing: 1 }}>ROLE</label>
            <select value={form.role} onChange={e => setForm(f => ({ ...f, role: e.target.value }))}>
              <option value="civilian">CIVILIAN</option>
              <option value="ngo_worker">NGO WORKER</option>
              <option value="journalist">JOURNALIST</option>
              <option value="medical">MEDICAL</option>
            </select>
          </div>

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
            {loading ? 'CREATING...' : 'CREATE ACCOUNT'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: 20, color: 'var(--text2)', fontSize: 12 }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: 'var(--red)' }}>LOGIN</Link>
        </p>
      </div>
    </div>
  )
}
