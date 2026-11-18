import { type FormEvent, useEffect, useState } from "react";
import {
  Badge,
  Button,
  Dialog,
  Field,
  Select,
  StatePanel,
} from "./ui/components";

type Company = {
  id: string;
  code: string;
  legal_name: string;
  is_active: boolean;
  version: number;
};

function companyFrom(value: unknown): Company {
  if (
    typeof value !== "object" ||
    value === null ||
    !("id" in value) ||
    typeof value.id !== "string" ||
    !("code" in value) ||
    typeof value.code !== "string" ||
    !("legal_name" in value) ||
    typeof value.legal_name !== "string" ||
    !("is_active" in value) ||
    typeof value.is_active !== "boolean" ||
    !("version" in value) ||
    typeof value.version !== "number" ||
    !Number.isInteger(value.version) ||
    value.version < 1
  )
    throw new Error("Invalid company response");
  return {
    id: value.id,
    code: value.code,
    legal_name: value.legal_name,
    is_active: value.is_active,
    version: value.version,
  };
}

export function Companies({ csrfToken }: { csrfToken: string }) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("");
  const [offset, setOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [editError, setEditError] = useState("");
  const [message, setMessage] = useState("");
  const [editing, setEditing] = useState<Company | null>(null);

  // biome-ignore lint/correctness/useExhaustiveDependencies: Retry and save refresh the same query.
  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    setCompanies([]);
    const params = new URLSearchParams({ q: search, offset: String(offset) });
    if (filter) params.set("active", filter);
    void fetch(`/api/companies?${params}`, {
      credentials: "same-origin",
      signal: controller.signal,
    })
      .then(async (response) => {
        if (!response.ok)
          throw new Error("Companies unavailable. Sign in again or retry.");
        const data: unknown = await response.json();
        if (!Array.isArray(data)) throw new Error("Invalid company response");
        const rows = data.map(companyFrom);
        if (!controller.signal.aborted) setCompanies(rows);
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError(
            "Companies unavailable. Check your session and connection, then retry.",
          );
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [search, filter, offset, reload]);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!editing) return;
    const values = new FormData(event.currentTarget);
    setSaving(true);
    setEditError("");
    setMessage("");
    try {
      const response = await fetch(`/api/companies/${editing.id}`, {
        method: "PATCH",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": csrfToken,
        },
        body: JSON.stringify({
          legal_name: values.get("legal_name"),
          is_active: values.get("active") === "true",
          version: editing.version,
        }),
      });
      if (response.status === 409)
        throw new Error(
          "This company changed. Close this form and refresh before editing again.",
        );
      if (!response.ok)
        throw new Error(
          "Unable to save. Check your access, session and company name.",
        );
      companyFrom(await response.json());
      setEditing(null);
      setMessage("Company saved.");
      setReload((value) => value + 1);
    } catch (failure) {
      setEditError(
        failure instanceof Error ? failure.message : "Unable to save company.",
      );
    } finally {
      setSaving(false);
    }
  }

  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">ORGANIZATION</p>
          <h1>Company Management</h1>
          <p className="muted">Legal companies you are authorized to manage.</p>
        </div>
      </div>
      <section className="card company-registry" aria-label="Company registry">
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
            label="Search companies"
            type="search"
            maxLength={100}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
          <Select
            label="Company status"
            value={filter}
            onChange={(event) => {
              setFilter(event.target.value);
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
          <p role="status">Loading companies…</p>
        ) : error ? (
          <StatePanel
            title="Companies unavailable"
            action={
              <Button onClick={() => setReload((value) => value + 1)}>
                Retry
              </Button>
            }
          >
            {error}
          </StatePanel>
        ) : companies.length === 0 ? (
          <StatePanel title="No authorized companies found">
            Try another search. A trusted operator must provision a company and
            grant your account access.
          </StatePanel>
        ) : (
          <ul className="company-list">
            {companies.slice(0, 20).map((company) => (
              <li key={company.id}>
                <div>
                  <span className="eyebrow">{company.code}</span>
                  <h2>{company.legal_name}</h2>
                </div>
                <Badge tone={company.is_active ? "success" : "neutral"}>
                  {company.is_active ? "Active" : "Inactive"}
                </Badge>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setEditing(company);
                    setEditError("");
                  }}
                  aria-label={`Edit ${company.legal_name}`}
                >
                  Edit
                </Button>
              </li>
            ))}
          </ul>
        )}
        <nav className="company-pagination" aria-label="Company pages">
          <Button
            variant="secondary"
            disabled={loading || offset === 0}
            onClick={() => setOffset((value) => Math.max(0, value - 20))}
          >
            Previous
          </Button>
          <span>Page {Math.floor(offset / 20) + 1}</span>
          <Button
            variant="secondary"
            disabled={loading || companies.length <= 20 || offset >= 10000}
            onClick={() => setOffset((value) => value + 20)}
          >
            Next
          </Button>
        </nav>
      </section>
      {editing && (
        <Dialog
          title={`Edit company ${editing.code}`}
          onClose={() => {
            if (!saving) setEditing(null);
          }}
        >
          <form className="company-edit" onSubmit={(event) => void save(event)}>
            <Field
              label="Legal company name"
              name="legal_name"
              defaultValue={editing.legal_name}
              required
              maxLength={200}
              disabled={saving}
            />
            <Select
              label="Status"
              name="active"
              defaultValue={String(editing.is_active)}
              disabled={saving}
            >
              <option value="true">Active</option>
              <option value="false">Inactive</option>
            </Select>
            <p className="small muted">
              Inactivation retains the company and its history.
            </p>
            {editError && <p role="alert">{editError}</p>}
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save company"}
            </Button>
          </form>
        </Dialog>
      )}
    </>
  );
}
