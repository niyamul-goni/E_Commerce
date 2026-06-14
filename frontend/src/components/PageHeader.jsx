export default function PageHeader({ title, subtitle, action }) {
  return (
    <div className="page-header">
      <div>
        <p className="eyebrow">E-Commerce Management System</p>
        <h1>{title}</h1>
        {subtitle ? <p className="page-header__subtitle">{subtitle}</p> : null}
      </div>
      {action ? <div className="page-header__action">{action}</div> : null}
    </div>
  );
}
