import { useState } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { Shield, Map, AlertTriangle, Home, LogOut, Users, Menu, X, Phone } from 'lucide-react'

export default function Navbar() {
  const { user, logout } = useAuth()
  const location = useLocation()
  const navigate = useNavigate()
  const [menuOpen, setMenuOpen] = useState(false)

  const handleLogout = () => { logout(); navigate('/login') }
  const isAdmin = user?.role === 'admin' || user?.role === 'ngo_worker'
  const active = (path) => location.pathname.startsWith(path)

  const links = [
    { to: '/map', icon: <Map size={15} />, label: 'MAP', always: true },
    { to: '/civil', icon: <Home size={15} />, label: 'CIVILIAN', always: true },
    { to: '/admin', icon: <Users size={15} />, label: 'ADMIN', adminOnly: true },
    { to: '/admin/sos', icon: <AlertTriangle size={15} />, label: 'SOS', adminOnly: true },
    { to: '/contacts', icon: <Phone size={15} />, label: 'CONTACTS', always: true },
  ].filter(l => l.always || (l.adminOnly && isAdmin))

  return (
    <nav style={{
      background: 'var(--bg2)', borderBottom: '1px solid var(--border)',
      padding: '0 16px', display: 'flex', alignItems: 'center',
      height: 56, position: 'sticky', top: 0, zIndex: 1000,
    }}>
      <Link to="/" style={{ display: 'flex', alignItems: 'center', gap: 8, marginRight: 'auto' }}>
        <Shield size={20} color="var(--red)" />
        <span style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: 13, letterSpacing: 2, color: 'var(--red)' }}>
          SAFEPASSAGE
        </span>
      </Link>

      {/* Desktop links */}
      <div style={{ display: 'flex', gap: 4, alignItems: 'center' }} className="nav-desktop">
        {links.map(l => (
          <Link key={l.to} to={l.to} style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '6px 12px', borderRadius: 3, fontSize: 11,
            fontFamily: 'var(--mono)', letterSpacing: 1,
            background: active(l.to) ? 'var(--red)' : 'transparent',
            color: active(l.to) ? '#fff' : 'var(--text2)',
          }}>{l.icon} {l.label}</Link>
        ))}
        <span style={{ color: 'var(--text2)', fontFamily: 'var(--mono)', fontSize: 11, marginLeft: 12 }}>
          {user?.display_name || user?.username || 'ANON'}
        </span>
        <button onClick={handleLogout} style={{
          background: 'transparent', color: 'var(--text2)',
          display: 'flex', alignItems: 'center', gap: 4, padding: '4px 8px', fontSize: 12,
        }}><LogOut size={14} /></button>
      </div>

      {/* Mobile burger */}
      <button onClick={() => setMenuOpen(o => !o)} className="nav-burger" style={{
        background: 'transparent', color: 'var(--text)', padding: 8, display: 'none',
      }}>
        {menuOpen ? <X size={20} /> : <Menu size={20} />}
      </button>

      {/* Mobile menu */}
      {menuOpen && (
        <div style={{
          position: 'fixed', top: 56, left: 0, right: 0, bottom: 0,
          background: 'var(--bg2)', zIndex: 999, padding: 24,
          display: 'flex', flexDirection: 'column', gap: 8,
        }}>
          {links.map(l => (
            <Link key={l.to} to={l.to} onClick={() => setMenuOpen(false)} style={{
              display: 'flex', alignItems: 'center', gap: 12,
              padding: '14px 16px', borderRadius: 4, fontSize: 14,
              fontFamily: 'var(--mono)', letterSpacing: 1,
              background: active(l.to) ? 'var(--red)' : 'var(--bg3)',
              color: active(l.to) ? '#fff' : 'var(--text)',
              border: '1px solid var(--border)',
            }}>{l.icon} {l.label}</Link>
          ))}
          <button onClick={handleLogout} style={{
            marginTop: 'auto', background: 'var(--bg3)', color: 'var(--text2)',
            padding: '12px', borderRadius: 4, fontFamily: 'var(--mono)',
            fontSize: 12, border: '1px solid var(--border)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
          }}><LogOut size={14} /> LOGOUT</button>
        </div>
      )}
    </nav>
  )
}
