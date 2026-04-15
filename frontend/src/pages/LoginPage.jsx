// src/pages/LoginPage.jsx — JWT login wired to /auth/login
import { useState, useEffect, useRef } from 'react'
import { Link, useNavigate, useLocation } from 'react-router-dom'
import { Eye, EyeOff, ArrowRight, CheckCircle } from 'lucide-react'
import { useAuthStore } from '../store/useAuthStore'
import LoginAnimation from '../components/auth/LoginAnimation'

function validate(email, password) {
  const errs = {}
  if (!email) errs.email = 'Email is required'
  else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) errs.email = 'Enter a valid email address'
  if (!password) errs.password = 'Password is required'
  else if (password.length < 8) errs.password = 'Password must be at least 8 characters'
  return errs
}

export default function LoginPage() {
  const location  = useLocation()
  const incoming  = location.state || {}          // { accountCreated?, email?, from? }

  const [email,     setEmail]     = useState(incoming.email || '')
  const [password,  setPassword]  = useState('')
  const [showPass,  setShowPass]  = useState(false)
  const [loading,   setLoading]   = useState(false)
  const [errors,    setErrors]    = useState({})
  const [formError, setFormError] = useState('')

  const passwordRef = useRef(null)
  const login       = useAuthStore(s => s.login)
  const navigate    = useNavigate()

  // Redirect destination after login
  const from = incoming.from?.pathname || '/app'

  // Auto-focus password when email was pre-filled from signup
  useEffect(() => {
    if (incoming.accountCreated && incoming.email) {
      // Small delay to let the page paint first
      setTimeout(() => passwordRef.current?.focus(), 120)
    }
  }, [])

  function handleBlur(field) {
    const errs = validate(email, password)
    setErrors(prev => ({ ...prev, [field]: errs[field] }))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    const errs = validate(email, password)
    if (Object.keys(errs).length) { setErrors(errs); return }

    setLoading(true)
    setFormError('')
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setFormError(err.message || 'Invalid email or password')
    } finally {
      setLoading(false)
    }
  }

  const inputCls = (field) =>
    `input-erebus w-full bg-erebus-bg text-erebus-text-1 rounded-lg px-4 py-3 text-[14px]
     border ${errors[field] ? 'border-erebus-red/70' : 'border-white/[0.10]'}`

  return (
    <div className="flex h-screen bg-erebus-bg">
      <LoginAnimation />

      {/* Right form panel */}
      <div className="flex-1 lg:flex-[0_0_45%] border-l border-white/[0.07] bg-erebus-surface flex items-center justify-center px-6 lg:px-10 overflow-y-auto">
        <div className="w-full max-w-sm py-10">

          <Link to="/" className="flex items-center gap-2 mb-10 w-fit group">
            <div className="w-7 h-7 rounded-full flex items-center justify-center border border-erebus-gold/50 font-serif text-erebus-gold text-sm bg-erebus-gold/[0.08]">
              E
            </div>
            <span className="font-serif text-[20px] text-erebus-text-1">EREBUS</span>
          </Link>

          {/* ── Account created success banner ── */}
          {incoming.accountCreated && (
            <div className="mb-6 px-4 py-3 rounded-lg bg-erebus-green/[0.08] border border-erebus-green/30 flex items-start gap-3">
              <CheckCircle size={16} className="text-erebus-green shrink-0 mt-0.5" />
              <div>
                <p className="text-[13px] font-semibold text-erebus-green">Account created successfully</p>
                <p className="text-[12px] text-erebus-text-3 mt-0.5">
                  Your email has been filled in — just enter your password to sign in.
                </p>
              </div>
            </div>
          )}

          <h1 className="font-serif text-[28px] text-erebus-text-1 mb-1">Welcome back</h1>
          <p className="text-[14px] text-erebus-text-2 mb-8">Sign in to your research workspace</p>

          {/* Form-level error */}
          {formError && (
            <div className="mb-5 px-4 py-3 rounded-lg bg-erebus-red/[0.08] border border-erebus-red/30 text-[13px] text-erebus-red">
              {formError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5" noValidate>
            {/* Email — pre-filled and locked if coming from signup */}
            <div>
              <label className="block text-[13px] text-erebus-text-2 mb-1.5">Email address</label>
              <input
                type="email" value={email}
                onChange={e => {
                  setEmail(e.target.value)
                  if (errors.email) setErrors(p => ({ ...p, email: undefined }))
                }}
                onBlur={() => handleBlur('email')}
                className={inputCls('email')}
                placeholder="you@example.com"
                autoComplete="email"
                // If pre-filled from signup, make it read-only so it's obvious
                readOnly={!!incoming.accountCreated}
                style={incoming.accountCreated ? { opacity: 0.75, cursor: 'default' } : {}}
              />
              {errors.email && <p className="mt-1.5 text-[12px] text-erebus-red">{errors.email}</p>}
              {incoming.accountCreated && (
                <p className="mt-1 text-[11px] font-mono text-erebus-gold">
                  ✓ Registered with this address
                </p>
              )}
            </div>

            {/* Password — auto-focused when coming from signup */}
            <div>
              <div className="flex justify-between mb-1.5">
                <label className="text-[13px] text-erebus-text-2">Password</label>
                <a href="#" className="text-[13px] text-erebus-gold hover:underline">Forgot password?</a>
              </div>
              <div className="relative">
                <input
                  ref={passwordRef}
                  type={showPass ? 'text' : 'password'} value={password}
                  onChange={e => {
                    setPassword(e.target.value)
                    if (errors.password) setErrors(p => ({ ...p, password: undefined }))
                  }}
                  onBlur={() => handleBlur('password')}
                  className={`${inputCls('password')} pr-11`}
                  placeholder="••••••••"
                  autoComplete="current-password"
                />
                <button type="button" onClick={() => setShowPass(p => !p)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-erebus-text-3 hover:text-erebus-text-2 transition-colors">
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
              {errors.password && <p className="mt-1.5 text-[12px] text-erebus-red">{errors.password}</p>}
            </div>

            <button
              type="submit" disabled={loading}
              className="w-full h-12 rounded-lg text-[14px] font-semibold btn-gold flex items-center justify-center gap-2 disabled:opacity-60 disabled:cursor-not-allowed"
            >
              {loading
                ? <span className="w-4 h-4 border-2 border-black/30 border-t-black rounded-full animate-spin" />
                : <><span>Sign in</span><ArrowRight size={15} /></>
              }
            </button>
          </form>

          {/* Divider + social (only show if not a fresh signup redirect) */}
          {!incoming.accountCreated && (
            <>
              <div className="flex items-center gap-3 my-6">
                <div className="flex-1 h-px bg-white/[0.07]" />
                <span className="text-[12px] font-mono text-erebus-text-3">or continue with</span>
                <div className="flex-1 h-px bg-white/[0.07]" />
              </div>
              <div className="grid grid-cols-2 gap-3">
                {['Google', 'Microsoft'].map(p => (
                  <button key={p} className="h-10 flex items-center justify-center gap-2 rounded-lg text-[13px] font-medium btn-ghost" disabled>
                    {p}
                  </button>
                ))}
              </div>
            </>
          )}

          <p className="text-center text-[13px] text-erebus-text-2 mt-6">
            No account?{' '}
            <Link to="/signup" className="text-erebus-gold hover:underline">Sign up free</Link>
          </p>
        </div>
      </div>
    </div>
  )
}
