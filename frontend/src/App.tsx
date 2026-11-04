import { useEffect, useState } from "react";
import { AuthPanel } from "./AuthPanel";
import { ApplicationShell } from "./shell/ApplicationShell";
import { Icon } from "./ui/Icon";
import { Button } from "./ui/components";

export function App() {
  const [status, setStatus] = useState("Connecting to API…");
  const [theme, setTheme] = useState(() => {
    try {
      return localStorage.getItem("erp-theme") === "dark" ? "dark" : "light";
    } catch {
      return "light";
    }
  });

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    try {
      localStorage.setItem("erp-theme", theme);
    } catch {
      /* Theme persistence is optional. */
    }
  }, [theme]);

  function toggleTheme() {
    setTheme((value) => (value === "light" ? "dark" : "light"));
  }

  useEffect(() => {
    const controller = new AbortController();
    void fetch("/api/bootstrap", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("API unavailable");
        const data: unknown = await response.json();
        if (
          typeof data !== "object" ||
          data === null ||
          !("name" in data) ||
          data.name !== "Manpower ERP" ||
          !("stage" in data) ||
          data.stage !== "bootstrap"
        )
          throw new Error("Unexpected API response");
        setStatus("API connected");
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setStatus("API unavailable. Check the local API and reload.");
      });
    return () => controller.abort();
  }, []);

  return (
    <AuthPanel
      renderAuthenticated={(panel, username, signOut, busy, error) => (
        <ApplicationShell
          accountPanel={panel}
          username={username}
          signOut={signOut}
          busy={busy}
          authError={error}
          status={status}
          theme={theme}
          toggleTheme={toggleTheme}
        />
      )}
      renderAnonymous={(panel) => (
        <div className="login-layout">
          <aside className="login-story">
            <div className="brand">
              <span className="brand-mark">
                M<span>·</span>
              </span>
              <span className="brand-copy">
                MANPOWER<span>ERP WORKSPACE</span>
              </span>
            </div>
            <div className="login-statement">
              <p className="eyebrow">PHILIPPINE MANPOWER SYSTEMS</p>
              <h1>Manpower ERP</h1>
              <p className="login-tagline">
                Clarity for every
                <br />
                part of your operation.
              </p>
              <p>
                One workspace for your people, contracts and accounting. Built
                around control, accountability and the details that matter.
              </p>
            </div>
            <div className="login-story-footer">
              <span className="gold-dot" />
              Development foundation · UI-001
            </div>
          </aside>
          <main className="login-main">
            <div className="login-toolbar">
              <span className="environment-label">DEVELOPMENT WORKSPACE</span>
              <Button
                variant="quiet"
                aria-label={`Switch to ${theme === "light" ? "dark" : "light"} theme`}
                onClick={toggleTheme}
              >
                <Icon name="sun" />
              </Button>
            </div>
            <div className="login-content">
              <p className="eyebrow">WELCOME TO YOUR WORKSPACE</p>
              <h2>Sign in to continue</h2>
              <p className="muted">
                Use your administrator-provisioned account.
              </p>
              {panel}
              <p role="status" className="login-status">
                {status}
              </p>
              <p className="small muted">
                Business modules are not available yet. Signing in grants no
                company or financial access.
              </p>
            </div>
            <footer className="login-footer">
              Protected sessions. Independent approvals.<span>PHILIPPINES</span>
            </footer>
          </main>
        </div>
      )}
    />
  );
}
