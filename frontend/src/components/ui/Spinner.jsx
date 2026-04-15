export default function Spinner({ size = 'md', className = '' }) {
  const sizes = {
    sm: 'w-3 h-3 border-[1.5px]',
    md: 'w-4 h-4 border-2',
    lg: 'w-6 h-6 border-2',
  }
  return (
    <span
      className={`inline-block rounded-full border-current/20 border-t-current animate-spin ${sizes[size] ?? sizes.md} ${className}`}
    />
  )
}
