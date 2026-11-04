import { type FormEvent, useState } from "react";

export function RecoveryForm() {
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  async function recover(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const values = new FormData(form);
    setBusy(true);
    setMessage("");
    setError("");
    try {
      const response = await fetch("/api/auth/reset-password", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: values.get("token"),
          new_password: values.get("recovery_password"),
        }),
      });
      if (response.status !== 204) throw new Error("Recovery failed");
      setMessage("Password reset. Sign in with your new password.");
    } catch {
      setError(
        "Unable to reset password. Ask your administrator for a new token or try later.",
      );
    } finally {
      form.reset();
      setBusy(false);
    }
  }

  return (
    <details>
      <summary>Reset password with an administrator token</summary>
      <p className="note">
        Ask your administrator to verify your identity and arrange independent
        approval. Tokens expire after 15 minutes.
      </p>
      {error && <p role="alert">{error}</p>}
      {message && <p aria-live="polite">{message}</p>}
      <form
        aria-label="Reset password"
        onSubmit={(event) => void recover(event)}
      >
        <label htmlFor="recovery-token">Recovery token</label>
        <input
          id="recovery-token"
          name="token"
          type="password"
          autoComplete="off"
          minLength={43}
          maxLength={43}
          required
        />
        <label htmlFor="recovery-password">Recovery password</label>
        <input
          id="recovery-password"
          name="recovery_password"
          type="password"
          autoComplete="new-password"
          minLength={15}
          maxLength={128}
          required
        />
        <button disabled={busy} type="submit">
          Reset password
        </button>
      </form>
    </details>
  );
}
