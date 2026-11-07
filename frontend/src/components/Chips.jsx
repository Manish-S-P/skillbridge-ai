export default function Chips({ items, variant = "" }) {
  if (!items || items.length === 0) return <span className="muted">None</span>;
  return (
    <div className="chips">
      {items.map((item, i) => (
        <span key={`${item}-${i}`} className={`chip ${variant}`}>
          {item}
        </span>
      ))}
    </div>
  );
}
