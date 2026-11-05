import { type ReactNode, useRef, useState } from "react";
import {
  Badge,
  Button,
  DataTable,
  Dialog,
  Field,
  StatePanel,
} from "../ui/components";
import { Icon } from "../ui/Icon";
import { Reference } from "../ui/Reference";
import { modules, type Page } from "./navigation";

export function ApplicationShell({
  username,
  accountPanel,
  signOut,
  busy,
  authError,
  status,
  theme,
  toggleTheme,
}: {
  username: string;
  accountPanel: ReactNode;
  signOut: () => void;
  busy: boolean;
  authError: string;
  status: string;
  theme: string;
  toggleTheme: () => void;
}) {
  const [page, setPage] = useState<Page>("dashboard");
  const [collapsed, setCollapsed] = useState(false);
  const [search, setSearch] = useState(false);
  const [mobileNavigation, setMobileNavigation] = useState(false);
  const [query, setQuery] = useState("");
  const [notifications, setNotifications] = useState(false);
  const main = useRef<HTMLElement>(null);
  const userMenu = useRef<HTMLDetailsElement>(null);
  const current = modules.find((module) => module.id === page);
  const title =
    current?.label ?? (page === "account" ? "My account" : "Design system");
  function navigate(next: Page) {
    setPage(next);
    setSearch(false);
    setMobileNavigation(false);
    setQuery("");
    if (userMenu.current) userMenu.current.open = false;
    requestAnimationFrame(() => {
      main.current?.focus({ preventScroll: true });
      window.scrollTo({ top: 0, behavior: "instant" });
    });
  }
  return (
    <div className={`app-shell ${collapsed ? "is-collapsed" : ""}`}>
      <a className="skip-link" href="#workspace">
        Skip to workspace
      </a>
      <aside className="sidebar" aria-label="Application sidebar">
        <button
          type="button"
          className="brand brand-button"
          onClick={() => navigate("dashboard")}
          title="Manpower ERP home"
        >
          <span className="brand-mark">
            M<span>·</span>
          </span>
          <span className="brand-copy">
            MANPOWER<span>ERP WORKSPACE</span>
          </span>
        </button>
        <div className="sidebar-label">PHILIPPINE OPERATIONS</div>
        <nav aria-label="Primary navigation">
          {[
            "Workspace",
            "Organization",
            "Accounting",
            "Insights",
            "System",
          ].map((group) => (
            <div className="nav-group" key={group}>
              <p className="nav-group-title">{group}</p>
              {modules
                .filter((module) => module.group === group)
                .map((module) => (
                  <button
                    type="button"
                    key={module.id}
                    className={`nav-item ${page === module.id ? "active" : ""}`}
                    aria-current={page === module.id ? "page" : undefined}
                    disabled={module.id === "administration"}
                    title={
                      module.id === "administration"
                        ? "Unavailable: server-verified capability required"
                        : module.label
                    }
                    aria-label={module.label}
                    onClick={() => navigate(module.id)}
                  >
                    <Icon name={module.icon} />
                    <span>{module.label}</span>
                    {module.id !== "dashboard" && (
                      <span className="nav-future" aria-hidden="true">
                        ·
                      </span>
                    )}
                  </button>
                ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <button
            type="button"
            className={`nav-item ${page === "reference" ? "active" : ""}`}
            aria-label="Design system"
            aria-current={page === "reference" ? "page" : undefined}
            title="Design system"
            onClick={() => navigate("reference")}
          >
            <Icon name="layout" />
            <span>Design system</span>
          </button>
          <div className="sidebar-note">
            <span className="gold-dot" />
            Development workspace<span>Business modules are not live</span>
          </div>
        </div>
      </aside>
      <div className="workspace-frame">
        <header className="app-header">
          <div className="header-leading">
            <Button
              variant="quiet"
              className="mobile-only"
              aria-label="Open navigation"
              onClick={() => setMobileNavigation(true)}
            >
              <Icon name="layout" />
            </Button>
            <Button
              variant="quiet"
              className="desktop-only"
              aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
              aria-expanded={!collapsed}
              onClick={() => setCollapsed((value) => !value)}
            >
              <Icon name="panel" />
            </Button>
            <span className="header-divider" />
            <div className="context-control">
              <label className="sr-only" htmlFor="organization-context">
                Company and branch context
              </label>
              <select
                id="organization-context"
                disabled
                aria-describedby="context-help"
              >
                <option>No authorized context</option>
              </select>
              <span id="context-help" className="sr-only">
                Company and branch scope APIs are not available. Selection never
                grants access.
              </span>
            </div>
          </div>
          <div className="header-actions">
            <Button
              variant="quiet"
              className="global-search"
              aria-label="Search workspace modules"
              onClick={() => setSearch(true)}
            >
              <Icon name="search" />
              <span>Search workspace</span>
            </Button>
            <Button
              variant="quiet"
              aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
              onClick={toggleTheme}
            >
              <Icon name="sun" />
            </Button>
            <Button
              variant="quiet"
              aria-label="Notifications"
              onClick={() => setNotifications(true)}
            >
              <Icon name="bell" />
            </Button>
            <details className="account-menu" ref={userMenu}>
              <summary aria-label={`${username}, user account menu`}>
                <span className="avatar" aria-hidden="true">
                  <Icon name="users" />
                </span>
                <span className="account-name">{username}</span>
                <span aria-hidden="true">⌄</span>
              </summary>
              <div className="account-popover">
                <p>
                  Signed in as <strong>{username}</strong>
                </p>
                <Button variant="quiet" onClick={() => navigate("account")}>
                  My account & password
                </Button>
                <Button variant="quiet" onClick={signOut} disabled={busy}>
                  Sign out
                </Button>
              </div>
            </details>
          </div>
        </header>
        <div className="breadcrumb-bar">
          <nav aria-label="Breadcrumb">
            <ol>
              <li>
                <button type="button" onClick={() => navigate("dashboard")}>
                  Workspace
                </button>
              </li>
              <li aria-current="page">{title}</li>
            </ol>
          </nav>
          <span className="environment-label">DEVELOPMENT</span>
        </div>
        <main id="workspace" className="workspace" ref={main} tabIndex={-1}>
          {authError && page !== "account" && (
            <p role="alert" className="auth-error">
              {authError}
            </p>
          )}
          {page === "dashboard" ? (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">YOUR OPERATIONS, IN ONE PLACE</p>
                  <h1>Workspace overview</h1>
                  <p className="muted">
                    A clear foundation for people, contracts and accounting.
                  </p>
                </div>
                <Badge tone="warning">Foundation stage</Badge>
              </div>
              <div className="workspace-banner">
                <div className="banner-icon">
                  <Icon name="building" />
                </div>
                <div>
                  <h2>Your company workspace starts here</h2>
                  <p>
                    Organizational setup is awaiting approved scope APIs. No
                    company or financial access is granted by signing in.
                  </p>
                </div>
                <Badge>Setup pending</Badge>
              </div>
              <div className="overview-grid">
                <section className="card foundation-card">
                  <div className="section-heading">
                    <h2>Workspace foundations</h2>
                    <span className="eyebrow">01 / GET ORIENTED</span>
                  </div>
                  <div className="foundation-row">
                    <span className="number-label">01</span>
                    <div>
                      <h3>Account & security</h3>
                      <p>Manage your password and end your session.</p>
                    </div>
                    <button
                      type="button"
                      className="icon-link"
                      aria-label="Open my account"
                      onClick={() => navigate("account")}
                    >
                      <Icon name="arrow" />
                    </button>
                  </div>
                  <div className="foundation-row">
                    <span className="number-label">02</span>
                    <div>
                      <h3>Company context</h3>
                      <p>
                        Authorized company and branch scopes are not available
                        yet.
                      </p>
                    </div>
                    <Badge>Pending</Badge>
                  </div>
                  <div className="foundation-row">
                    <span className="number-label">03</span>
                    <div>
                      <h3>Consistent workspace</h3>
                      <p>
                        Explore the controls used across future ERP screens.
                      </p>
                    </div>
                    <button
                      type="button"
                      className="icon-link"
                      aria-label="Explore design system"
                      onClick={() => navigate("reference")}
                    >
                      <Icon name="arrow" />
                    </button>
                  </div>
                </section>
                <section className="card status-card">
                  <div className="section-heading">
                    <h2>System status</h2>
                    <Icon name="settings" />
                  </div>
                  <p role="status" className="connection-status">
                    {status}
                  </p>
                  <dl className="status-list">
                    <div>
                      <dt>Session</dt>
                      <dd>
                        <Badge tone="success">Authenticated</Badge>
                      </dd>
                    </div>
                    <div>
                      <dt>Company scope</dt>
                      <dd>Unavailable</dd>
                    </div>
                    <div>
                      <dt>Business modules</dt>
                      <dd>Not implemented</dd>
                    </div>
                  </dl>
                  <p className="small muted">
                    API status checks bootstrap metadata, not database
                    readiness. Security acceptance remains pending.
                  </p>
                </section>
              </div>
              <section className="card modules-card">
                <div className="section-heading">
                  <div>
                    <h2>Module directory</h2>
                    <p className="muted">
                      Planned destinations. No business records or totals are
                      shown.
                    </p>
                  </div>
                  <Badge>Preview only</Badge>
                </div>
                <div className="module-table">
                  <DataTable
                    caption="ERP module availability"
                    columns={["Module", "Purpose", "Availability"]}
                    rows={modules
                      .filter((module) => module.id !== "dashboard")
                      .map((module) => ({
                        id: module.id,
                        cells: [
                          module.id === "administration" ? (
                            <span key="name" className="module-name">
                              {module.label}
                            </span>
                          ) : (
                            <button
                              type="button"
                              key="name"
                              className="text-link"
                              onClick={() => navigate(module.id)}
                            >
                              {module.label}
                            </button>
                          ),
                          module.description,
                          <Badge key="availability">
                            {module.id === "administration"
                              ? "Access unavailable"
                              : "Not implemented"}
                          </Badge>,
                        ],
                      }))}
                  />
                </div>
                <ul className="mobile-module-directory">
                  {modules
                    .filter((module) => module.id !== "dashboard")
                    .map((module) => (
                      <li key={module.id}>
                        <button
                          type="button"
                          disabled={module.id === "administration"}
                          onClick={() => navigate(module.id)}
                        >
                          <Icon name={module.icon} />
                          <span>
                            {module.label}
                            <small>
                              {module.id === "administration"
                                ? "Access unavailable"
                                : "Not implemented"}
                            </small>
                          </span>
                          <Icon name="arrow" />
                        </button>
                      </li>
                    ))}
                </ul>
              </section>
            </>
          ) : page === "account" ? (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">PERSONAL SETTINGS</p>
                  <h1>My account</h1>
                  <p className="muted">
                    Password changes revoke existing sessions. You will sign in
                    again.
                  </p>
                </div>
              </div>
              <div className="card account-card">{accountPanel}</div>
            </>
          ) : page === "reference" ? (
            <Reference />
          ) : (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">{current?.group} / MODULE PREVIEW</p>
                  <h1>{title}</h1>
                  <p className="muted">{current?.description}</p>
                </div>
                <Badge>Not implemented</Badge>
              </div>
              <section className="card">
                <StatePanel
                  title="This module is not available yet"
                  action={
                    <Button
                      variant="secondary"
                      onClick={() => navigate("dashboard")}
                    >
                      Back to overview
                    </Button>
                  }
                >
                  This is a navigation placeholder. No business data is loaded
                  or created. Future access requires server-authorized
                  organizational scopes.
                </StatePanel>
              </section>
            </>
          )}
        </main>
        <footer className="workspace-footer">
          <span>
            MANPOWER ERP <span className="footer-separator">/</span> PHILIPPINES
          </span>
          <span>UI-001 · Development foundation</span>
        </footer>
      </div>
      <nav className="mobile-bottom-bar" aria-label="Quick navigation">
        <button
          type="button"
          aria-current={page === "dashboard" ? "page" : undefined}
          onClick={() => navigate("dashboard")}
        >
          <Icon name="dashboard" />
          Home
        </button>
        <button type="button" onClick={() => setSearch(true)}>
          <Icon name="search" />
          Search
        </button>
        <button type="button" onClick={() => setMobileNavigation(true)}>
          <Icon name="layout" />
          Modules
        </button>
        <button
          type="button"
          aria-current={page === "account" ? "page" : undefined}
          onClick={() => navigate("account")}
        >
          <Icon name="users" />
          Account
        </button>
      </nav>
      {mobileNavigation && (
        <Dialog
          title="Workspace navigation"
          onClose={() => setMobileNavigation(false)}
        >
          <p className="small muted">
            Business destinations are previews. No company access is granted.
          </p>
          <nav
            aria-label="Mobile module navigation"
            className="mobile-module-list"
          >
            {modules.map((module) => (
              <Button
                key={module.id}
                variant="quiet"
                disabled={module.id === "administration"}
                onClick={() => navigate(module.id)}
              >
                <Icon name={module.icon} />
                {module.label}
                {module.id !== "dashboard" && (
                  <Badge>
                    {module.id === "administration" ? "Unavailable" : "Preview"}
                  </Badge>
                )}
              </Button>
            ))}
            <Button variant="quiet" onClick={() => navigate("reference")}>
              <Icon name="layout" />
              Design system
            </Button>
          </nav>
        </Dialog>
      )}
      {search && (
        <Dialog title="Search workspace" onClose={() => setSearch(false)}>
          <Field
            label="Find a module"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Try clients, contracts, reports…"
            hint="Module names only. Record search is not implemented."
          />
          <ul className="search-results">
            {modules
              .filter(
                (module) =>
                  module.id !== "administration" &&
                  module.label
                    .toLowerCase()
                    .includes(query.trim().toLowerCase()),
              )
              .map((module) => (
                <li key={module.id}>
                  <button type="button" onClick={() => navigate(module.id)}>
                    <Icon name={module.icon} />
                    <span>{module.label}</span>
                    <Badge>
                      {module.id === "dashboard"
                        ? "Workspace"
                        : "Not implemented"}
                    </Badge>
                  </button>
                </li>
              ))}
          </ul>
          {!modules.some(
            (module) =>
              module.id !== "administration" &&
              module.label.toLowerCase().includes(query.trim().toLowerCase()),
          ) && (
            <StatePanel title="No matching modules">
              Try a different module name.
            </StatePanel>
          )}
        </Dialog>
      )}
      {notifications && (
        <Dialog title="Notifications" onClose={() => setNotifications(false)}>
          <StatePanel title="No notification service connected">
            Activity and approval notifications will appear here once authorized
            backend services are available.
          </StatePanel>
        </Dialog>
      )}
    </div>
  );
}
