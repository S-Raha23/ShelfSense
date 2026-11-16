export default function Spinner({ fullPage = false, label = "Loading" }) {
  return (
    <div className={fullPage ? "spinner-page" : "spinner-wrap"} role="status" aria-label={label}>
      <div className="spinner" />
    </div>
  );
}
