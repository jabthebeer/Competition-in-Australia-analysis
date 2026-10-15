// An in-page confirmation step. Browser dialogs (window.confirm) are blocked in some
// hosts, such as embedded viewers, and are awkward for screen-reader users.
import { useState } from "react";

export function ConfirmButton(props: {
  label: string;
  question: string;
  confirmLabel: string;
  onConfirm: () => void;
  className?: string;
  testId?: string;
}) {
  const [asking, setAsking] = useState(false);
  if (!asking) {
    return (
      <button type="button" className={props.className} onClick={() => setAsking(true)} data-testid={props.testId}>
        {props.label}
      </button>
    );
  }
  return (
    <span className="confirm" role="group" aria-label={props.question}>
      <span className="confirm-question">{props.question}</span>
      <button
        type="button"
        className="danger"
        autoFocus
        onClick={() => {
          setAsking(false);
          props.onConfirm();
        }}
        data-testid={props.testId ? `${props.testId}-confirm` : undefined}
      >
        {props.confirmLabel}
      </button>
      <button type="button" onClick={() => setAsking(false)}>
        Cancel
      </button>
    </span>
  );
}
