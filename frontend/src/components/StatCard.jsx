export default function StatCard({ label, value, hint }) {
  return (
    <article className="stat-card card">
      <p className="stat-card__label">{label}</p>
      <h3 className="stat-card__value">{value}</h3>
      {hint ? <p className="stat-card__hint">{hint}</p> : null}
    </article>
  );
}
