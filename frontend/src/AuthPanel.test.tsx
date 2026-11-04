import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { AuthPanel } from "./AuthPanel";

const account = {
  id: "test-user",
  username: "alice",
  csrf_token: "a".repeat(64),
};
const json = (value: unknown, status = 200) =>
  new Response(JSON.stringify(value), { status });

describe("account access", () => {
  it("signs in and sends CSRF on sign out", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(json({}, 401))
      .mockResolvedValueOnce(json(account))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthPanel />);
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled(),
    );
    fireEvent.change(screen.getByLabelText("Username"), {
      target: { value: "alice" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "synthetic password phrase" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Sign in" }));
    expect(await screen.findByText("alice")).toBeVisible();
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(
      await screen.findByRole("button", { name: "Sign in" }),
    ).toBeVisible();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/auth/logout",
      expect.objectContaining({
        method: "POST",
        headers: { "X-CSRF-Token": account.csrf_token },
      }),
    );
  });

  it("reports generic login failure and clears the password", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(json({}, 401))
        .mockResolvedValueOnce(json({}, 401)),
    );
    render(<AuthPanel />);
    await screen.findByRole("button", { name: "Sign in" });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "wrong synthetic password" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Sign in" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Sign-in failed",
    );
    expect(screen.getByLabelText("Password")).toHaveValue("");
  });

  it("changes password with CSRF and returns to sign in", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(json(account))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);
    render(<AuthPanel />);
    await screen.findByText("alice");
    fireEvent.change(screen.getByLabelText("Current password"), {
      target: { value: "old synthetic password" },
    });
    fireEvent.change(screen.getByLabelText("New password"), {
      target: { value: "new synthetic password" },
    });
    fireEvent.submit(screen.getByRole("form", { name: "Change password" }));
    expect(
      await screen.findByText("Password changed. Sign in again."),
    ).toBeVisible();
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/auth/password",
      expect.objectContaining({
        headers: expect.objectContaining({
          "X-CSRF-Token": account.csrf_token,
        }),
      }),
    );
  });

  it("keeps the session visible when logout fails", async () => {
    vi.stubGlobal(
      "fetch",
      vi
        .fn()
        .mockResolvedValueOnce(json(account))
        .mockResolvedValueOnce(json({}, 503)),
    );
    render(<AuthPanel />);
    await screen.findByText("alice");
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to sign out",
    );
    expect(screen.getByText("alice")).toBeVisible();
  });
});
