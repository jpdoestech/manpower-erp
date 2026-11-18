import { type FormEvent, useEffect, useState } from "react";
import {
  Badge,
  Button,
  Dialog,
  Field,
  Select,
  StatePanel,
} from "./ui/components";

type Choice = {
  id: string;
  code: string;
  name: string;
  is_active: boolean;
  period?: string;
};
type Unit = Choice & {
  company_id: string;
  valid_from: string;
  valid_to: string | null;
  version: number;
  head_office_id?: string;
  head_office_name?: string;
};

function choiceFrom(value: unknown): Choice {
  if (
    typeof value !== "object" ||
    value === null ||
    !("id" in value) ||
    typeof value.id !== "string" ||
    !("code" in value) ||
    typeof value.code !== "string" ||
    !("is_active" in value) ||
    typeof value.is_active !== "boolean"
  )
    throw new Error("Invalid organization response");
  const name =
    "legal_name" in value
      ? value.legal_name
      : "name" in value
        ? value.name
        : null;
  if (typeof name !== "string") throw new Error("Invalid organization name");
  const period =
    "valid_from" in value && typeof value.valid_from === "string"
      ? `${value.valid_from} — ${"valid_to" in value && typeof value.valid_to === "string" ? value.valid_to : "Open ended"}`
      : undefined;
  return {
    id: value.id,
    code: value.code,
    name,
    is_active: value.is_active,
    period,
  };
}

function unitFrom(value: unknown, company: string, branch: boolean): Unit {
  const choice = choiceFrom(value);
  if (
    typeof value !== "object" ||
    value === null ||
    !("company_id" in value) ||
    value.company_id !== company ||
    !("valid_from" in value) ||
    typeof value.valid_from !== "string" ||
    !("valid_to" in value) ||
    (value.valid_to !== null && typeof value.valid_to !== "string") ||
    !("version" in value) ||
    typeof value.version !== "number" ||
    !Number.isInteger(value.version) ||
    value.version < 1
  )
    throw new Error("Invalid hierarchy response");
  const parent = "head_office_id" in value ? value.head_office_id : undefined;
  const parentName =
    "head_office_name" in value ? value.head_office_name : undefined;
  if (branch && (typeof parent !== "string" || typeof parentName !== "string"))
    throw new Error("Missing head office");
  return {
    ...choice,
    company_id: company,
    valid_from: value.valid_from,
    valid_to: value.valid_to,
    version: value.version,
    head_office_id: typeof parent === "string" ? parent : undefined,
    head_office_name: typeof parentName === "string" ? parentName : undefined,
  };
}

function RegistryPicker({
  endpoint,
  label,
  selected,
  disabled,
  onSelect,
}: {
  endpoint: string;
  label: string;
  selected: Choice | null;
  disabled: boolean;
  onSelect: (value: Choice | null) => void;
}) {
  const [choices, setChoices] = useState<Choice[]>([]);
  const [input, setInput] = useState("");
  const [query, setQuery] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [retry, setRetry] = useState(0);
  // biome-ignore lint/correctness/useExhaustiveDependencies: Explicit retries reload the current page.
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setChoices([]);
    const params = new URLSearchParams({ q: query, offset: String(offset) });
    void fetch(`${endpoint}${endpoint.includes("?") ? "&" : "?"}${params}`, {
      credentials: "same-origin",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Options unavailable");
        const data: unknown = await response.json();
        if (!Array.isArray(data)) throw new Error("Invalid response");
        const values = data.map(choiceFrom);
        if (!controller.signal.aborted) setChoices(values);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            `${label} options unavailable. Check your access and retry.`,
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [endpoint, query, offset, retry, label]);

  function search() {
    onSelect(null);
    setOffset(0);
    setQuery(input.trim());
    setRetry((value) => value + 1);
  }
  return (
    <div className="hierarchy-picker">
      <div className="hierarchy-picker-search">
        <Field
          label={`Find ${label.toLowerCase()}`}
          type="search"
          value={input}
          maxLength={100}
          disabled={disabled}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              search();
            }
          }}
        />
        <Button
          type="button"
          variant="secondary"
          disabled={disabled || loading}
          onClick={search}
        >
          Find
        </Button>
      </div>
      {error ? (
        <p role="alert">
          {error}{" "}
          <Button type="button" onClick={() => setRetry((value) => value + 1)}>
            Retry options
          </Button>
        </p>
      ) : (
        <Select
          label={label}
          value={selected?.id ?? ""}
          disabled={disabled || loading}
          onChange={(event) =>
            onSelect(
              choices.find((item) => item.id === event.target.value) ?? null,
            )
          }
        >
          <option value="">
            {loading ? "Loading…" : `Select ${label.toLowerCase()}`}
          </option>
          {choices.slice(0, 20).map((item) => (
            <option key={item.id} value={item.id}>
              {item.code} · {item.name}
              {item.is_active ? "" : " (inactive)"}
            </option>
          ))}
        </Select>
      )}
      {selected?.period && (
        <p className="small muted">Parent period {selected.period}</p>
      )}
      {!loading && !error && choices.length === 0 && (
        <p className="small muted">No authorized options found.</p>
      )}
      <div className="hierarchy-picker-pages">
        <Button
          type="button"
          variant="quiet"
          aria-label={`Previous ${label.toLowerCase()} options`}
          disabled={disabled || loading || offset === 0}
          onClick={() => {
            onSelect(null);
            setOffset((value) => value - 20);
          }}
        >
          Previous
        </Button>
        <span className="small">Page {Math.floor(offset / 20) + 1}</span>
        <Button
          type="button"
          variant="quiet"
          aria-label={`Next ${label.toLowerCase()} options`}
          disabled={
            disabled || loading || choices.length <= 20 || offset >= 10000
          }
          onClick={() => {
            onSelect(null);
            setOffset((value) => value + 20);
          }}
        >
          Next
        </Button>
      </div>
    </div>
  );
}

export function Hierarchy({
  kind,
  csrfToken,
}: {
  kind: "head-offices" | "branches";
  csrfToken: string;
}) {
  const branch = kind === "branches";
  const title = branch ? "Branches" : "Head Offices";
  const singular = branch ? "branch" : "head office";
  const [company, setCompany] = useState<Choice | null>(null);
  const [units, setUnits] = useState<Unit[]>([]);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [active, setActive] = useState("");
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");
  const [reload, setReload] = useState(0);
  const [editing, setEditing] = useState<Unit | "new" | null>(null);
  const [parent, setParent] = useState<Choice | null>(null);
  const [saving, setSaving] = useState(false);
  const [formError, setFormError] = useState("");
  const endpoint = company
    ? `/api/companies/${encodeURIComponent(company.id)}/${kind}`
    : "";
  // biome-ignore lint/correctness/useExhaustiveDependencies: Successful writes and retries refresh the current scoped query.
  useEffect(() => {
    if (!company) return;
    const controller = new AbortController();
    const params = new URLSearchParams({ q: search, offset: String(offset) });
    if (active) params.set("active", active);
    setUnits([]);
    setLoading(true);
    setError("");
    void fetch(`${endpoint}?${params}`, {
      credentials: "same-origin",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok) throw new Error("Hierarchy unavailable");
        const data: unknown = await response.json();
        if (!Array.isArray(data)) throw new Error("Invalid hierarchy response");
        const rows = data.map((item) => unitFrom(item, company.id, branch));
        if (!controller.signal.aborted) setUnits(rows);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Records unavailable. Check your session, hierarchy access and connection.",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [company, endpoint, search, active, offset, reload, branch]);

  function chooseCompany(value: Choice | null) {
    setCompany(value);
    setUnits([]);
    setOffset(0);
    setEditing(null);
    setError("");
    setMessage("");
  }

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing || !company) return;
    if (branch && editing === "new" && !parent) {
      setFormError("Choose a head office.");
      return;
    }
    const values = new FormData(event.currentTarget);
    const body = {
      name: values.get("name"),
      valid_to: values.get("valid_to") || null,
      is_active: values.get("active") === "true",
      ...(editing === "new"
        ? {
            code: values.get("code"),
            valid_from: values.get("valid_from"),
            ...(branch ? { head_office_id: parent?.id } : {}),
          }
        : { version: editing.version }),
    };
    setSaving(true);
    setFormError("");
    setMessage("");
    try {
      const response = await fetch(
        editing === "new"
          ? endpoint
          : `${endpoint}/${encodeURIComponent(editing.id)}`,
        {
          method: editing === "new" ? "POST" : "PATCH",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
            "X-CSRF-Token": csrfToken,
          },
          body: JSON.stringify(body),
        },
      );
      if (response.status === 409)
        throw new Error(
          "Conflict. Refresh the record and check duplicate codes, parent status and child periods.",
        );
      if (response.status === 422)
        throw new Error(
          "Check the code, name and dates. The period must fit its parent and an active record cannot already be expired.",
        );
      if (!response.ok)
        throw new Error(
          "Unable to save. Check your access, session and connection.",
        );
      unitFrom(await response.json(), company.id, branch);
      setEditing(null);
      setMessage(`${branch ? "Branch" : "Head office"} saved.`);
      setReload((value) => value + 1);
    } catch (failure) {
      setFormError(
        failure instanceof Error ? failure.message : "Unable to save.",
      );
    } finally {
      setSaving(false);
    }
  }

  const existing = editing && editing !== "new" ? editing : null;
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ORGANIZATION</p>
          <h1>{title}</h1>
          <p className="muted">
            {branch
              ? "Branches within their legal company and head office."
              : "Head offices within their legal company."}
          </p>
        </div>
        <Button
          disabled={!company?.is_active || saving || loading || Boolean(error)}
          onClick={() => {
            setEditing("new");
            setParent(null);
            setFormError("");
          }}
        >
          Add {singular}
        </Button>
      </div>
      <section
        className="card company-registry"
        aria-label={`${title} registry`}
      >
        <RegistryPicker
          label="Company"
          endpoint="/api/companies?hierarchy=true"
          selected={company}
          disabled={saving}
          onSelect={chooseCompany}
        />
        {company ? (
          <>
            <p className="hierarchy-context">
              <strong>{company.code}</strong> · {company.name}
              {company.is_active ? "" : " · Inactive company"}
            </p>
            <form
              className="company-search"
              onSubmit={(event) => {
                event.preventDefault();
                setOffset(0);
                setSearch(query.trim());
                setReload((value) => value + 1);
              }}
            >
              <Field
                label={`Search ${title.toLowerCase()}`}
                type="search"
                value={query}
                maxLength={100}
                onChange={(event) => setQuery(event.target.value)}
              />
              <Select
                label="Record status"
                value={active}
                onChange={(event) => {
                  setActive(event.target.value);
                  setOffset(0);
                }}
              >
                <option value="">All statuses</option>
                <option value="true">Active</option>
                <option value="false">Inactive</option>
              </Select>
              <Button type="submit" disabled={loading}>
                Search
              </Button>
            </form>
            {message && <p role="status">{message}</p>}
            {loading ? (
              <p role="status">Loading records…</p>
            ) : error ? (
              <StatePanel
                title="Records unavailable"
                action={
                  <Button onClick={() => setReload((value) => value + 1)}>
                    Retry records
                  </Button>
                }
              >
                {error}
              </StatePanel>
            ) : units.length === 0 ? (
              <StatePanel title={`No ${title.toLowerCase()} found`}>
                Add a record or change the search and status filters.
              </StatePanel>
            ) : (
              <ul className="company-list">
                {units.slice(0, 20).map((unit) => (
                  <li key={unit.id}>
                    <div>
                      <span className="eyebrow">{unit.code}</span>
                      <h2>{unit.name}</h2>
                      {branch && (
                        <p className="small muted">{unit.head_office_name}</p>
                      )}
                      <p className="small muted">
                        {unit.valid_from} — {unit.valid_to ?? "Open ended"}
                      </p>
                    </div>
                    <Badge tone={unit.is_active ? "success" : "neutral"}>
                      {unit.is_active ? "Active" : "Inactive"}
                    </Badge>
                    <Button
                      variant="secondary"
                      aria-label={`Edit ${unit.name}`}
                      onClick={() => {
                        setEditing(unit);
                        setFormError("");
                      }}
                    >
                      Edit
                    </Button>
                  </li>
                ))}
              </ul>
            )}
            <nav className="company-pagination" aria-label={`${title} pages`}>
              <Button
                variant="secondary"
                disabled={loading || offset === 0}
                onClick={() => setOffset((value) => value - 20)}
              >
                Previous
              </Button>
              <span>Page {Math.floor(offset / 20) + 1}</span>
              <Button
                variant="secondary"
                disabled={loading || units.length <= 20 || offset >= 10000}
                onClick={() => setOffset((value) => value + 20)}
              >
                Next
              </Button>
            </nav>
          </>
        ) : (
          <StatePanel title="Choose a company">
            Hierarchy access requires an explicit operator grant for your
            account.
          </StatePanel>
        )}
      </section>
      {editing && company && (
        <Dialog
          title={`${existing ? "Edit" : "Add"} ${singular}`}
          onClose={() => {
            if (!saving) setEditing(null);
          }}
        >
          <form className="company-edit" onSubmit={(event) => void save(event)}>
            <p className="small muted">
              {company.code} · {company.name}
            </p>
            {existing ? (
              <p>
                <strong>{existing.code}</strong>
                {branch ? ` · ${existing.head_office_name}` : ""}
              </p>
            ) : (
              <>
                <Field
                  label="Code"
                  name="code"
                  minLength={2}
                  maxLength={32}
                  pattern="[A-Za-z0-9][A-Za-z0-9_-]{1,31}"
                  required
                  disabled={saving}
                  hint="2–32 letters, numbers, hyphens or underscores."
                />
                {branch && (
                  <RegistryPicker
                    label="Head office"
                    endpoint={`/api/companies/${encodeURIComponent(company.id)}/head-offices?active=true`}
                    selected={parent}
                    disabled={saving}
                    onSelect={setParent}
                  />
                )}
              </>
            )}
            <Field
              label="Name"
              name="name"
              defaultValue={existing?.name ?? ""}
              required
              maxLength={200}
              disabled={saving}
            />
            <div className="hierarchy-dates">
              <Field
                label="Effective from"
                name="valid_from"
                type="date"
                required
                defaultValue={
                  existing?.valid_from ??
                  new Intl.DateTimeFormat("en-CA", {
                    timeZone: "Asia/Manila",
                  }).format(new Date())
                }
                disabled={Boolean(existing) || saving}
              />
              <Field
                label="Effective until"
                name="valid_to"
                type="date"
                defaultValue={existing?.valid_to ?? ""}
                disabled={saving}
                hint="Leave blank for an open period."
              />
            </div>
            <Select
              label="Status"
              name="active"
              defaultValue={String(existing?.is_active ?? true)}
              disabled={saving}
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </Select>
            <p className="small muted">
              Company, parent, code and start date stay fixed. Inactivation
              preserves history.
            </p>
            {formError && <p role="alert">{formError}</p>}
            <Button
              type="submit"
              disabled={saving || (branch && !existing && !parent)}
            >
              {saving ? "Saving…" : `Save ${singular}`}
            </Button>
          </form>
        </Dialog>
      )}
    </>
  );
}
