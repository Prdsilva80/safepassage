import { useTranslation } from 'react-i18next'

const LANGUAGES = [
  { code: 'en', label: 'EN' },
  { code: 'uk', label: 'УК' },
  { code: 'ar', label: 'ع' },
  { code: 'fr', label: 'FR' },
  { code: 'es', label: 'ES' },
  { code: 'pt', label: 'PT' },
  { code: 'pt-BR', label: 'BR' },
]

export default function LanguageSelector() {
  const { i18n } = useTranslation()
  const current = i18n.language

  return (
    <div style={{
      display: 'flex', gap: 2, alignItems: 'center',
      background: 'var(--bg3)', borderRadius: 4,
      padding: '3px 4px', border: '1px solid var(--border)',
    }}>
      {LANGUAGES.map(l => (
        <button
          key={l.code}
          onClick={() => i18n.changeLanguage(l.code)}
          style={{
            background: current === l.code ? 'var(--red)' : 'transparent',
            color: current === l.code ? '#fff' : 'var(--text2)',
            padding: '2px 7px', borderRadius: 3,
            fontSize: 10, fontFamily: 'var(--mono)',
            border: 'none', cursor: 'pointer',
            fontWeight: current === l.code ? 700 : 400,
            transition: 'all 0.15s',
          }}
        >
          {l.label}
        </button>
      ))}
    </div>
  )
}