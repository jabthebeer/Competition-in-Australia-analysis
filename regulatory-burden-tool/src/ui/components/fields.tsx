// Accessible form fields: every input has a visible label, help text is linked with
// aria-describedby, and validation messages are announced. Numbers are typed as text
// (inputMode="decimal") so commas and "$" can be pasted and nothing rounds silently.
import { useEffect, useId, useState, type ReactNode } from "react";
import { dec } from "../../engine/decimal";
import type { Quantity } from "../../engine/index";

export function Help({ id, children }: { id?: string; children: ReactNode }) {
  return (
    <p className="help" id={id}>
      {children}
    </p>
  );
}

interface Base {
  label: string;
  help?: ReactNode;
  testId?: string;
}

export function TextField(props: Base & { value: string; onChange: (v: string) => void; multiline?: boolean; required?: boolean; placeholder?: string }) {
  const id = useId();
  const helpId = props.help ? `${id}-help` : undefined;
  const common = {
    id,
    value: props.value,
    "aria-describedby": helpId,
    required: props.required,
    placeholder: props.placeholder,
    "data-testid": props.testId,
  };
  return (
    <div className="field">
      <label htmlFor={id}>{props.label}</label>
      {props.help && <Help id={helpId}>{props.help}</Help>}
      {props.multiline ? (
        <textarea {...common} rows={3} onChange={(e) => props.onChange(e.target.value)} />
      ) : (
        <input {...common} type="text" onChange={(e) => props.onChange(e.target.value)} />
      )}
    </div>
  );
}

export function SelectField<T extends string>(
  props: Base & { value: T; options: readonly { value: T; label: string }[]; onChange: (v: T) => void; disabled?: boolean },
) {
  const id = useId();
  const helpId = props.help ? `${id}-help` : undefined;
  return (
    <div className="field">
      <label htmlFor={id}>{props.label}</label>
      {props.help && <Help id={helpId}>{props.help}</Help>}
      <select id={id} value={props.value} aria-describedby={helpId} disabled={props.disabled} data-testid={props.testId} onChange={(e) => props.onChange(e.target.value as T)}>
        {props.options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}

export function RadioGroup<T extends string>(
  props: Base & { value: T; options: readonly { value: T; label: string; help?: string }[]; onChange: (v: T) => void; inline?: boolean },
) {
  const name = useId();
  const helpId = props.help ? `${name}-help` : undefined;
  return (
    <fieldset className={`field radio-group${props.inline ? " inline" : ""}`} aria-describedby={helpId} data-testid={props.testId}>
      <legend>{props.label}</legend>
      {props.help && <Help id={helpId}>{props.help}</Help>}
      {props.options.map((o) => (
        <label key={o.value} className="radio">
          <input type="radio" name={name} value={o.value} checked={props.value === o.value} onChange={() => props.onChange(o.value)} />
          <span>
            {o.label}
            {o.help && <span className="radio-help">{o.help}</span>}
          </span>
        </label>
      ))}
    </fieldset>
  );
}

export function Checkbox(props: Base & { checked: boolean; onChange: (v: boolean) => void; disabled?: boolean }) {
  const id = useId();
  const helpId = props.help ? `${id}-help` : undefined;
  return (
    <div className="field checkbox">
      <input id={id} type="checkbox" checked={props.checked} disabled={props.disabled} aria-describedby={helpId} data-testid={props.testId} onChange={(e) => props.onChange(e.target.checked)} />
      <label htmlFor={id}>{props.label}</label>
      {props.help && <Help id={helpId}>{props.help}</Help>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Numbers

interface NumberOpts {
  /** Display multiplier, e.g. 100 to show a 0–1 share as a percentage. */
  scale?: number;
  min?: number;
  max?: number;
  integer?: boolean;
  prefix?: string;
  unit?: string;
}

function toDisplay(n: number, scale = 1): string {
  return scale === 1 ? String(n) : dec(n).times(scale).toFixed();
}

function parseNumber(text: string, o: NumberOpts): { value?: number; error?: string } {
  const cleaned = text.replace(/[,\s$%]/g, "");
  if (cleaned === "") return { error: "Enter a number" };
  if (!/^-?\d*\.?\d+$|^-?\d+\.$/.test(cleaned)) return { error: "Enter a number, like 2 or 2.5" };
  const scaled = o.scale && o.scale !== 1 ? dec(cleaned).dividedBy(o.scale).toNumber() : Number(cleaned);
  if (!Number.isFinite(scaled)) return { error: "Enter a number" };
  if (o.integer && !Number.isInteger(scaled)) return { error: "Enter a whole number" };
  const shownMin = o.min !== undefined ? toDisplay(o.min, o.scale) : undefined;
  const shownMax = o.max !== undefined ? toDisplay(o.max, o.scale) : undefined;
  if (o.min !== undefined && scaled < o.min) return { error: `Enter ${shownMin} or more` };
  if (o.max !== undefined && scaled > o.max) return { error: `Enter ${shownMax} or less` };
  return { value: scaled };
}

/** A number input that only reports valid values and keeps what the user typed while they type. */
function NumberInput(props: NumberOpts & { id: string; value: number; onChange: (n: number) => void; describedBy?: string; ariaLabel?: string; testId?: string }) {
  const [text, setText] = useState(toDisplay(props.value, props.scale));
  const [error, setError] = useState<string | undefined>();
  useEffect(() => {
    // Follow outside changes (e.g. loading a file) unless the user is mid-edit on an equal value.
    const parsed = parseNumber(text, props);
    if (parsed.value !== props.value) {
      setText(toDisplay(props.value, props.scale));
      setError(undefined);
    }
  }, [props.value]);
  const errId = `${props.id}-error`;
  return (
    <span className="number-input">
      {props.prefix && <span className="affix" aria-hidden="true">{props.prefix}</span>}
      <input
        id={props.id}
        type="text"
        inputMode="decimal"
        value={text}
        aria-label={props.ariaLabel}
        aria-invalid={error ? true : undefined}
        aria-describedby={[props.describedBy, error ? errId : undefined].filter(Boolean).join(" ") || undefined}
        data-testid={props.testId}
        onChange={(e) => {
          setText(e.target.value);
          const parsed = parseNumber(e.target.value, props);
          setError(parsed.error);
          if (parsed.value !== undefined) props.onChange(parsed.value);
        }}
        onBlur={() => {
          if (error) {
            setText(toDisplay(props.value, props.scale));
            setError(undefined);
          }
        }}
      />
      {props.unit && <span className="affix" aria-hidden="true">{props.unit}</span>}
      {error && (
        <span className="error" id={errId} role="alert">
          {error}
        </span>
      )}
    </span>
  );
}

export function formatQuantity(q: Quantity | undefined, scale = 1, unit = ""): string {
  if (q === undefined) return "—";
  const f = (n: number) => `${toDisplay(n, scale)}${unit}`;
  return typeof q === "number" ? f(q) : `${f(q.low)}–${f(q.high)}`;
}

function sameQuantity(a: Quantity | undefined, b: Quantity | undefined): boolean {
  return JSON.stringify(a) === JSON.stringify(b);
}

/**
 * A quantity: a single value, or a low–high range whose midpoint is used as the point
 * estimate (A-07). With `current`, shows whether the reformed value differs from today's.
 */
export function QuantityField(
  props: Base & NumberOpts & { value: Quantity; onChange: (q: Quantity) => void; current?: Quantity; allowRange?: boolean; highlight?: boolean },
) {
  const id = useId();
  const helpId = props.help ? `${id}-help` : undefined;
  const isRange = typeof props.value !== "number";
  const changed = props.current !== undefined && !sameQuantity(props.current, props.value);
  const { scale, min, max, integer, prefix, unit } = props;
  const opts = { scale, min, max, integer, prefix, unit };
  const unitText = unit ? ` ${unit}` : "";
  return (
    <div className={`field quantity${changed ? " changed" : ""}${props.highlight ? " highlight" : ""}`} data-testid={props.testId}>
      <label htmlFor={id}>
        {props.label}
        {changed && <span className="badge changed-badge">Changed</span>}
      </label>
      {props.help && <Help id={helpId}>{props.help}</Help>}
      {typeof props.value === "number" ? (
        <NumberInput {...opts} id={id} value={props.value} describedBy={helpId} onChange={(n) => props.onChange(n)} testId={props.testId ? `${props.testId}-input` : undefined} />
      ) : (
        <span className="range">
          <NumberInput {...opts} id={id} ariaLabel={`${props.label}: low`} value={props.value.low} describedBy={helpId} onChange={(n) => props.onChange({ low: n, high: Math.max(n, (props.value as { high: number }).high) })} />
          <span aria-hidden="true">to</span>
          <NumberInput {...opts} id={`${id}-high`} ariaLabel={`${props.label}: high`} value={props.value.high} describedBy={helpId} onChange={(n) => props.onChange({ low: Math.min(n, (props.value as { low: number }).low), high: n })} />
          <span className="midpoint">Point estimate (midpoint): {formatQuantity(dec(props.value.low).plus(props.value.high).dividedBy(2).toNumber(), scale ?? 1)}{unitText}</span>
        </span>
      )}
      {props.allowRange !== false && (
        <label className="range-toggle">
          <input
            type="checkbox"
            checked={isRange}
            onChange={(e) => {
              const v = props.value;
              props.onChange(e.target.checked ? { low: typeof v === "number" ? v : v.low, high: typeof v === "number" ? v : v.high } : typeof v === "number" ? v : dec(v.low).plus(v.high).dividedBy(2).toNumber());
            }}
          />
          Enter a range
        </label>
      )}
      {changed && <p className="was">Current regime: {formatQuantity(props.current, scale ?? 1, unitText)}</p>}
    </div>
  );
}

/** A whole number such as a year. */
export function IntegerField(props: Base & { value: number; onChange: (n: number) => void; min?: number; max?: number; unit?: string }) {
  const id = useId();
  const helpId = props.help ? `${id}-help` : undefined;
  return (
    <div className="field">
      <label htmlFor={id}>{props.label}</label>
      {props.help && <Help id={helpId}>{props.help}</Help>}
      <NumberInput id={id} value={props.value} integer min={props.min} max={props.max} unit={props.unit} describedBy={helpId} onChange={props.onChange} testId={props.testId} />
    </div>
  );
}
