import {
  type ButtonHTMLAttributes,
  type InputHTMLAttributes,
  type ReactNode,
  useEffect,
  useId,
  useRef,
  useState,
} from "react";

export function Button({
  variant = "primary",
  className = "",
  type = "button",
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "quiet" | "danger";
}) {
  return (
    <button
      type={type}
      className={`button button-${variant} ${className}`}
      {...props}
    />
  );
}

export function Field({
  label,
  hint,
  error,
  ...props
}: InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  error?: string;
}) {
  const generated = useId();
  const id = props.id ?? generated;
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <input
        {...props}
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={error || hint ? `${id}-help` : undefined}
      />
      {(hint || error) && (
        <p id={`${id}-help`} className={error ? "field-error" : "field-hint"}>
          {error ?? hint}
        </p>
      )}
    </div>
  );
}

export function Select({
  label,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label: string }) {
  const id = useId();
  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      <select {...props} id={id}>
        {children}
      </select>
    </div>
  );
}

export function SearchableDropdown({
  label,
  options,
  ...props
}: Omit<InputHTMLAttributes<HTMLInputElement>, "list"> & {
  label: string;
  options: readonly string[];
  hint?: string;
}) {
  const id = useId();
  return (
    <>
      <Field {...props} label={label} list={id} type="search" />
      <datalist id={id}>
        {options.map((option) => (
          <option key={option} value={option} />
        ))}
      </datalist>
    </>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "success" | "warning" | "danger";
}) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function DataTable({
  caption,
  columns,
  rows,
}: {
  caption: string;
  columns: readonly string[];
  rows: { id: string; cells: ReactNode[] }[];
}) {
  return (
    // biome-ignore lint/a11y/noNoninteractiveTabindex: Keyboard users must be able to scroll a wide table region.
    <section className="table-scroll" tabIndex={0} aria-label={caption}>
      <table>
        <caption>{caption}</caption>
        <thead>
          <tr>
            {columns.map((column) => (
              <th scope="col" key={column}>
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.length ? (
            rows.map((row) => (
              <tr key={row.id}>
                {row.cells.map((cell, index) => (
                  <td key={columns[index]}>{cell}</td>
                ))}
              </tr>
            ))
          ) : (
            <tr>
              <td colSpan={columns.length} className="table-empty">
                No records to display.
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  );
}

export function Dialog({
  title,
  children,
  onClose,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const previous = document.activeElement;
    const dialog = ref.current;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (previous instanceof HTMLElement && previous.isConnected)
        previous.focus();
    };
  }, []);
  function dismiss() {
    ref.current?.close();
    onClose();
  }
  return (
    <dialog
      ref={ref}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        dismiss();
      }}
    >
      <div className="dialog-heading">
        <h2 id={titleId}>{title}</h2>
        <Button variant="quiet" onClick={dismiss} aria-label="Close dialog">
          ×
        </Button>
      </div>
      {children}
    </dialog>
  );
}

export function ConfirmDialog({
  title,
  children,
  confirmLabel,
  onConfirm,
  onClose,
}: {
  title: string;
  children: ReactNode;
  confirmLabel: string;
  onConfirm: () => void;
  onClose: () => void;
}) {
  return (
    <Dialog title={title} onClose={onClose}>
      <p>{children}</p>
      <div className="actions">
        <Button variant="secondary" onClick={onClose}>
          Cancel
        </Button>
        <Button variant="danger" onClick={onConfirm}>
          {confirmLabel}
        </Button>
      </div>
    </Dialog>
  );
}

export function Tabs({
  label,
  items,
}: {
  label: string;
  items: { label: string; content: ReactNode }[];
}) {
  const [active, setActive] = useState(0);
  const id = useId();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);
  return (
    <>
      <div className="tabs" role="tablist" aria-label={label}>
        {items.map((item, index) => (
          <button
            key={item.label}
            ref={(node) => {
              refs.current[index] = node;
            }}
            type="button"
            id={`${id}-tab-${index}`}
            role="tab"
            aria-selected={active === index}
            aria-controls={`${id}-panel-${index}`}
            tabIndex={active === index ? 0 : -1}
            onClick={() => setActive(index)}
            onKeyDown={(event) => {
              let next: number;
              if (event.key === "ArrowRight")
                next = (active + 1) % items.length;
              else if (event.key === "ArrowLeft")
                next = (active + items.length - 1) % items.length;
              else if (event.key === "Home") next = 0;
              else if (event.key === "End") next = items.length - 1;
              else return;
              event.preventDefault();
              setActive(next);
              refs.current[next]?.focus();
            }}
          >
            {item.label}
          </button>
        ))}
      </div>
      {items.map((item, index) => {
        return (
          <div
            key={item.label}
            id={`${id}-panel-${index}`}
            role="tabpanel"
            aria-labelledby={`${id}-tab-${index}`}
            // biome-ignore lint/a11y/noNoninteractiveTabindex: WAI tab pattern requires keyboard access to panel content.
            tabIndex={0}
            hidden={active !== index}
          >
            {item.content}
          </div>
        );
      })}
    </>
  );
}

export function StatePanel({
  kind = "empty",
  title,
  children,
  action,
}: {
  kind?: "empty" | "error" | "unauthorized";
  title: string;
  children: ReactNode;
  action?: ReactNode;
}) {
  return (
    <div
      className={`state-panel state-${kind}`}
      role={kind === "error" ? "alert" : undefined}
    >
      <span className="state-symbol" aria-hidden="true">
        {kind === "error" ? "!" : kind === "unauthorized" ? "⊘" : "◇"}
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
      {action}
    </div>
  );
}

export function Skeleton({ label = "Loading content" }: { label?: string }) {
  return (
    <div role="status" aria-label={label} className="skeleton">
      <span />
      <span />
      <span />
    </div>
  );
}

export function Toast({
  message,
  onDismiss,
}: {
  message: string;
  onDismiss: () => void;
}) {
  return (
    <div className="toast">
      <p role="status">{message}</p>
      <Button
        variant="quiet"
        onClick={onDismiss}
        aria-label="Dismiss notification"
      >
        ×
      </Button>
    </div>
  );
}
