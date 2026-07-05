export default function FormField({ label, error, className = '', as, children, ...props }) {
  const Element = as === 'textarea' ? 'textarea' : as === 'select' ? 'select' : 'input';

  return (
    <label className={`field ${className}`.trim()}>
      <span className="field__label">{label}</span>
      <Element className="field__control" {...props}>
        {children}
      </Element>
      {error ? <span className="field__error">{error}</span> : null}
    </label>
  );
}
