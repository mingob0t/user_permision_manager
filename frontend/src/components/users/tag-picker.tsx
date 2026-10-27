/** Selector de etiquetas (chips) de selección múltiple. */

export function TagPicker<T extends { id: number; name: string }>({
  options,
  selected,
  onChange,
  empty,
}: {
  options: T[];
  selected: number[];
  onChange: (ids: number[]) => void;
  empty: string;
}) {
  if (options.length === 0) {
    return <p className="text-xs text-label">{empty}</p>;
  }
  return (
    <div className="flex flex-wrap gap-2">
      {options.map((option) => {
        const on = selected.includes(option.id);
        // DIS-008: chip de 48 px con foco visible.
        return (
          <button
            key={option.id}
            type="button"
            aria-pressed={on}
            onClick={() =>
              onChange(on ? selected.filter((id) => id !== option.id) : [...selected, option.id])
            }
            className={`inline-flex min-h-12 min-w-12 items-center justify-center rounded-full border px-3 text-xs outline-none transition-colors focus-visible:ring-2 focus-visible:ring-primary ${
              on
                ? 'border-primary bg-primary/15 text-primary-text'
                : 'border-panel-border text-label hover:text-body-text'
            }`}
          >
            {option.name}
          </button>
        );
      })}
    </div>
  );
}
