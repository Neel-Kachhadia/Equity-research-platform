// src/pages/SignupPage.jsx
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Eye, EyeOff, ArrowRight, Check } from 'lucide-react'
import SignupAnimation from '../components/auth/SignupAnimation'
import { useAuthStore } from '../store/useAuthStore'

const ROLES   = ['Retail Analyst', 'Fund Manager', 'Research Intern', 'Other']
const SECTORS = ['FMCG', 'IT', 'NBFC', 'Pharma', 'Auto', 'Real Estate', 'Infra', 'Energy']

const STRENGTH_META = [
  null,
  { label: 'Weak',   color: 'bg-erebus-red',   text: 'text-erebus-red'   },
  { label: 'Fair',   color: 'bg-erebus-amber',  text: 'text-erebus-amber' },
  { label: 'Good',   color: 'bg-erebus-amber',  text: 'text-erebus-amber' },
  { label: 'Strong', color: 'bg-erebus-green',  text: 'text-erebus-green' },
]

function validateField(field, value, allValues) {
  switch (field) {
    case 'name':
      if (!value.trim()) return 'Full name is required'
      if (value.trim().length < 2) return 'Name must be at least 2 characters'
      return ''
    case 'email':
      if (!value.trim()) return 'Email address is required'
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return 'Enter a valid email address'
      return ''
    case 'password':
      if (!value) return 'Password is required'
      if (value.length < 8) return 'Password must be at least 8 characters'
      return ''
    default:
      return ''
  }
}

export default function SignupPage() {
  const [form,    setForm]    = useState({ name: '', email: '', org: '', password: '' })
  const [errors,  setErrors]  = useState({})
  const [touched, setTouched] = useState({})
  const [showPass, setShowPass] = useState(false)
  const [role,    setRole]    = useState('Retail Analyst')
  const [sectors, setSectors] = useState([])
  const [agreed,  setAgreed]  = useState(false)
  const [loading, setLoading] = useState(false)
  const [formError, setFormError] = useState('')
  const navigate = useNavigate()

  function handleChange(field, value) {
    setForm(f => ({ ...f, [field]: value }))
    if (touched[field]) {
      setErrors(e => ({ ...e, [field]: validateField(field, value, form) }))
    }
  }

  function handleBlur(field) {
    setTouched(t => ({ ...t, [field]: true }))
    setErrors(e => ({ ...e, [field]: validateField(field, form[field], form) }))
  }

  function toggleSector(s) {
    setSectors(prev => prev.includes(s) ? prev.filter(x => x !== s) : [...prev, s])
  }

  const strength = form.password.length === 0 ? 0
    : form.password.length < 6  ? 1
    : form.password.length < 10 ? 2
    : form.password.length < 14 ? 3 : 4

  const register = useAuthStore(s => s.register)

  async function handleSubmit(e) {
    e.preventDefault()
    const fields  = ['name', 'email', 'password']
    const newErrs = {}
    fields.forEach(f => { newErrs[f] = validateField(f, form[f], form) })
    setErrors(newErrs)
    setTouched({ name: true, email: true, password: true })
    if (Object.values(newErrs).some(Boolean) || !agreed) return
    setLoading(true)
    setFormError('')
    try {
      await register(form.name, form.email, form.password)
      // Don't log in yet — send to login page with email pre-filled
      navigate('/login', {
        replace: true,
        state: { accountCreated: true, email: form.email },
      })
    } catch (err) {
      setFormError(err.message || 'Registration failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = (field) =>
    `input-erebus w-full bg-erebus-bg text-erebus-text-1 rounded-lg px-4 py-3 text-[14px] border
     ${errors[field] && touched[field] ? 'border-erebus-red/60' : 'border-white/[0.10]'}`

  const isValid  = (field) => touched[field] && !errors[field] && form[field]

  return (
    <div className="flex h-screen bg-erebus-bg">
      <SignupAnimation />

      <div className="flex-1 lg:flex-[0_0_45%] border-l border-white/[0.07] bg-erebus-surface flex items-center justify-center px-6 lg:px-10 overflow-y-auto">
        <div className="w-full max-w-sm py-10">

          <Link to="/" className="flex items-center gap-2 mb-8 w-fit">
            <div className="w-7 h-7 rounded-full flex items-center justify-center border border-erebus-gold/50 font-serif text-erebus-gold text-sm bg-erebus-gold/[0.08]">
              E
            </div>
            <span className="font-serif text-[20px] text-erebus-text-1">EREBUS</span>
          </Link>

          <h1 className="font-serif text-[28px] text-erebus-text-1 mb-1">Create your workspace</h1>
          <p className="text-[14px] text-erebus-text-2 mb-7">Free forever on the Starter plan</p>

          {formError && (
            <div className="mb-5 px-4 py-3 rounded-lg bg-erebus-red/[0.08] border border-erebus-red/30 text-[13px] text-erebus-red">
              {formError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4" noValidate>

            {/* Full name */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">Full name</label>
              <div className="relative">
                <input
                  value={form.name}
                  onChange={e => handleChange('name', e.target.value)}
                  onBlur={() => handleBlur('name')}
                  className={inputCls('name')}
                  placeholder="Riya Sharma"
                />
                {isValid('name') && (
                  <Check size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-erebus-green" />
                )}
              </div>
              {errors.name && touched.name && (
                <p className="mt-1.5 text-[12px] text-erebus-red">{errors.name}</p>
              )}
            </div>

            {/* Work email */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">Work email</label>
              <div className="relative">
                <input
                  type="email"
                  value={form.email}
                  onChange={e => handleChange('email', e.target.value)}
                  onBlur={() => handleBlur('email')}
                  className={inputCls('email')}
                  placeholder="you@firm.com"
                />
                {isValid('email') && (
                  <Check size={14} className="absolute right-3 top-1/2 -translate-y-1/2 text-erebus-green" />
                )}
              </div>
              {errors.email && touched.email && (
                <p className="mt-1.5 text-[12px] text-erebus-red">{errors.email}</p>
              )}
            </div>

            {/* Organisation (optional) */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">
                Organisation <span className="text-erebus-text-3">(optional)</span>
              </label>
              <input
                value={form.org}
                onChange={e => handleChange('org', e.target.value)}
                className="input-erebus w-full bg-erebus-bg text-erebus-text-1 rounded-lg px-4 py-3 text-[14px] border border-white/[0.10]"
                placeholder="Leave blank if independent"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">Password</label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  value={form.password}
                  onChange={e => handleChange('password', e.target.value)}
                  onBlur={() => handleBlur('password')}
                  className={`${inputCls('password')} pr-11`}
                  placeholder="Min. 8 characters"
                />
                <button
                  type="button"
                  onClick={() => setShowPass(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-erebus-text-3 hover:text-erebus-text-2 transition-colors"
                >
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {/* Strength meter */}
              {form.password.length > 0 && (
                <div className="flex items-center gap-2 mt-2">
                  <div className="flex gap-1 flex-1">
                    {[1,2,3,4].map(seg => (
                      <div
                        key={seg}
                        className={`flex-1 h-1 rounded-full transition-all duration-300
                          ${strength >= seg ? STRENGTH_META[strength]?.color ?? 'bg-erebus-gold' : 'bg-white/[0.06]'}`}
                      />
                    ))}
                  </div>
                  {STRENGTH_META[strength] && (
                    <span className={`text-[11px] font-mono ${STRENGTH_META[strength].text}`}>
                      {STRENGTH_META[strength].label}
                    </span>
                  )}
                </div>
              )}
              {errors.password && touched.password && (
                <p className="mt-1.5 text-[12px] text-erebus-red">{errors.password}</p>
              )}
              {!errors.password && strength > 0 && strength < 3 && (
                <p className="mt-1.5 text-[12px] text-erebus-text-3">
                  Use 10+ characters with numbers and symbols for a strong password
                </p>
              )}
            </div>

            {/* Role */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-2">Your role</label>
              <div className="flex flex-wrap gap-2">
                {ROLES.map(r => (
                  <button
                    key={r} type="button" onClick={() => setRole(r)}
                    className={`px-3 py-1.5 rounded-full text-[12px] font-medium transition-all duration-150 border
                      ${role === r
                        ? 'bg-erebus-gold/[0.10] border-erebus-gold/40 text-erebus-gold'
                        : 'bg-transparent border-white/[0.10] text-erebus-text-2 hover:border-white/[0.20]'
                      }`}
                  >
                    {r}
                  </button>
                ))}
              </div>
            </div>

            {/* Sector chips */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-2">
                Sector interest <span className="text-erebus-text-3">(optional)</span>
              </label>
              <div className="flex flex-wrap gap-2">
                {SECTORS.map(s => (
                  <button
                    key={s} type="button" onClick={() => toggleSector(s)}
                    className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-[12px] font-medium transition-all duration-150 border
                      ${sectors.includes(s)
                        ? 'bg-erebus-gold/[0.10] border-erebus-gold/40 text-erebus-gold'
                        : 'bg-transparent border-white/[0.10] text-erebus-text-2 hover:border-white/[0.20]'
                      }`}
                  >
                    {sectors.includes(s) && <Check size={10} />}
                    {s}
                  </button>
                ))}
              </div>
            </div>

            {/* Terms */}
            <label className="flex items-start gap-2.5 cursor-pointer">
              <input
                type="checkbox" checked={agreed}
                onChange={e => setAgreed(e.target.checked)}
                className="mt-0.5 cursor-pointer accent-erebus-gold"
              />
              <span className="text-[13px] text-erebus-text-2">
                I agree to the{' '}
                <a href="#" className="text-erebus-gold hover:underline">Terms of Service</a>
                {' '}and{' '}
                <a href="#" className="text-erebus-gold hover:underline">Privacy Policy</a>
              </span>
            </label>

            <button
              type="submit"
              disabled={!agreed || loading}
              className="w-full h-12 rounded-lg text-[14px] font-semibold btn-gold flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading
                ? <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                : <><span>Create account</span><ArrowRight size={15} /></>
              }
            </button>
          </form>

          <p className="text-center text-[13px] text-erebus-text-2 mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-erebus-gold hover:underline">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
