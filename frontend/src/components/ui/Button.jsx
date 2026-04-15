export default function Button({
  children,
  variant  = 'primary',
  size     = 'md',
  disabled = false,
  loading  = false,
  onClick,
  className = '',
  ...rest
}) {
  const base = 'inline-flex items-center justify-center gap-2 font-medium rounded-md transition-all duration-150 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer'

  const variants = {
    primary: 'bg-erebus-gold text-erebus-bg hover:bg-[#D4B55C]',
    ghost:   'border border-white/[0.15] text-erebus-text-1 hover:border-erebus-gold hover:text-erebus-gold',
    danger:  'bg-erebus-red text-white hover:bg-[#D94F4F]',
  }

  const sizes = {
    sm: 'text-[13px] px-3 py-1.5',
    md: 'text-[14px] px-[18px] py-2',
    lg: 'text-[16px] px-7 py-[14px]',
  }

  return (
    <button
      disabled={disabled || loading}
      onClick={onClick}
      className={`${base} ${variants[variant] ?? variants.primary} ${sizes[size] ?? sizes.md} ${className}`}
      {...rest}
    >
      {loading
        ? <span className="w-4 h-4 border-2 border-current/30 border-t-current rounded-full animate-spin" />
        : children
      }
    </button>
  )
}
