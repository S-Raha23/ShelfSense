import { PERIOD_OPTIONS } from "../hooks/usePeriod";

export default function PeriodSelect({ value, onChange }) {
  return (
    <div className="segmented" role="radiogroup" aria-label="Date range">
      {PERIOD_OPTIONS.map((days) => (
        <button
          key={days}
          role="radio"
          aria-checked={value === days}
          className={value === days ? "is-active" : ""}
          onClick={() => onChange(days)}
        >
          {days}d
        </button>
      ))}
    </div>
  );
}
