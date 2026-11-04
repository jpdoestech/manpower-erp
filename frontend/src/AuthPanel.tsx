import { type FormEvent, type ReactNode, useEffect, useState } from "react";
import { RecoveryForm } from "./RecoveryForm";

type Account = { id: string; username: string; csrf_token: string };

async function accountFrom(response: Response): Promise<Account> {
  if (!response.ok) throw new Error("Authentication failed");
  const data: unknown = await response.json();
  if (
    typeof data !== "object" ||
    data === null ||
    !("id" in data) ||
    typeof data.id !== "string" ||
    !("username" in data) ||
    typeof data.username !== "string" ||
    !("csrf_token" in data) ||
    typeof data.csrf_token !== "string" ||
    !/^[a-f0-9]{64}$/.test(data.csrf_token)
  )
    throw new Error("Invalid session response");
  return { id: data.id, username: data.username, csrf_token: data.csrf_token };
}

export function AuthPanel({
  renderAuthenticated,
  renderAnonymous,
}: {
  renderAuthenticated?: (
    panel: ReactNode,
    username: string,
    signOut: () => void,
    busy: boolean,
    error: string,
  ) => ReactNode;
  renderAnonymous?: (panel: ReactNode) => ReactNode;
} = {}) {
  const [account, setAccount] = useState<Account | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void fetch("/api/auth/me", {
      signal: controller.signal,
      credentials: "same-origin",
    })
      .then(async (response) => {
        if (response.status !== 401) setAccount(await accountFrom(response));
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setError("Session unavailable. Check the connection and reload.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setBusy(false);
      });
    return () => controller.abort();
  }, []);

  async function signIn(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: values.get("username"),
          password: values.get("password"),
        }),
      });
      setAccount(await accountFrom(response));
    } catch {
      setError("Sign-in failed. Check your credentials or try again later.");
    } finally {
      form.reset();
      setBusy(false);
    }
  }

  async function signOut() {
    if (!account) return;
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/auth/logout", {
        method: "POST",
        credentials: "same-origin",
        headers: { "X-CSRF-Token": account.csrf_token },
      });
      if (response.status !== 204 && response.status !== 401)
        throw new Error("Logout failed");
      setAccount(null);
    } catch {
      setError("Unable to sign out. Try again before leaving this browser.");
    } finally {
      setBusy(false);
    }
  }

  async function changePassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!account) return;
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const response = await fetch("/api/auth/password", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": account.csrf_token,
        },
        body: JSON.stringify({
          current_password: values.get("current_password"),
          new_password: values.get("new_password"),
        }),
      });
      if (response.status !== 204) throw new Error("Password change failed");
      setAccount(null);
      setMessage("Password changed. Sign in again.");
    } catch {
      setError(
        "Unable to change password. Check your current password or sign in again.",
      );
    } finally {
      form.reset();
      setBusy(false);
    }
  }

  const panel = (
    <section className="auth" aria-labelledby="account-title">
      <h2 id="account-title">Account access</h2>
      {error && <p role="alert">{error}</p>}
      {message && <p aria-live="polite">{message}</p>}
      {account ? (
        <>
          <p>
            Signed in as <strong>{account.username}</strong>
          </p>
          <button type="button" disabled={busy} onClick={() => void signOut()}>
            Sign out
          </button>
          <form
            onSubmit={(event) => void changePassword(event)}
            aria-label="Change password"
          >
            <label htmlFor="current-password">Current password</label>
            <input
              id="current-password"
              name="current_password"
              type="password"
              autoComplete="current-password"
              required
              maxLength={128}
            />
            <label htmlFor="new-password">New password</label>
            <input
              id="new-password"
              name="new_password"
              type="password"
              autoComplete="new-password"
              required
              minLength={15}
              maxLength={128}
              aria-describedby="password-guidance"
            />
            <p id="password-guidance" className="note">
              Use a passphrase of 15–128 characters.
            </p>
            <button disabled={busy} type="submit">
              Change password
            </button>
          </form>
        </>
      ) : (
        <form onSubmit={(event) => void signIn(event)} aria-label="Sign in">
          <label htmlFor="username">Username</label>
          <input
            id="username"
            name="username"
            autoComplete="username"
            required
            minLength={3}
            maxLength={64}
          />
          <label htmlFor="password">Password</label>
          <input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
            maxLength={128}
          />
          <button type="submit" disabled={busy}>
            {busy ? "Please wait…" : "Sign in"}
          </button>
        </form>
      )}
      {!account && <RecoveryForm />}
    </section>
  );
  return account && renderAuthenticated
    ? renderAuthenticated(
        panel,
        account.username,
        () => void signOut(),
        busy,
        error,
      )
    : !account && renderAnonymous
      ? renderAnonymous(panel)
      : panel;
}
