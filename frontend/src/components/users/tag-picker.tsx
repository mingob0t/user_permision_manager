import { ToggleChip } from '../toggle-chip';

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
        return (
          <ToggleChip
            key={option.id}
            pressed={on}
            onClick={() =>
              onChange(on ? selected.filter((id) => id !== option.id) : [...selected, option.id])
            }
          >
            {option.name}
          </ToggleChip>
        );
      })}
    </div>
  );
}
