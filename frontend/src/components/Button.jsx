export default function Button({ children, variant = 'primary', className = '', loading = false, type = 'button', ...props }) {
  const classes = ['button', `button--${variant}`, className].filter(Boolean).join(' ');

  return (
    <button className={classes} type={type} disabled={loading || props.disabled} {...props}>
      {loading ? 'Please wait...' : children}
    </button>
  );
}
