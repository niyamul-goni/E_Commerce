export default function QuantityStepper({ value, onChange, min = 1, max = 999 }) {
  return (
    <div className="quantity-stepper">
      <button type="button" onClick={() => onChange(Math.max(min, Number(value) - 1))}>
        -
      </button>
      <input
        type="number"
        value={value}
        min={min}
        max={max}
        onChange={(event) => onChange(Number(event.target.value))}
      />
      <button type="button" onClick={() => onChange(Math.min(max, Number(value) + 1))}>
        +
      </button>
    </div>
  );
}
