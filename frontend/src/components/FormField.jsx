export default function FormField({ label, error, className = '', ...props }) {
  const isTextArea = props.as === 'textarea';
  const isSelect = props.as === 'select';
  const Element = isTextArea ? 'textarea' : isSelect ? 'select' : 'input';

  return (
    <label className={`field ${className}`.trim()}>
      <span className="field__label">{label}</span>
      <Element className="field__control" {...props} />
      {error ? <span className="field__error">{error}</span> : null}
    </label>
  );
}
