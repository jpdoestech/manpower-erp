import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "../App";

const account = {
  id: "synthetic-user",
  username: "example-user",
  csrf_token: "a".repeat(64),
};
function mockApi(logoutStatus = 204) {
  const request = vi.fn((url: string) =>
    Promise.resolve(
      url === "/api/bootstrap"
        ? Response.json({ name: "Manpower ERP", stage: "bootstrap" })
        : url === "/api/auth/logout"
          ? new Response(null, { status: logoutStatus })
          : Response.json(account),
    ),
  );
  vi.stubGlobal("fetch", request);
  return request;
}

describe("authenticated application shell", () => {
  it.each([401, 503, 200])(
    "does not render a shell for unavailable or invalid session %s",
    async (status) => {
      vi.stubGlobal(
        "fetch",
        vi.fn((url: string) =>
          Promise.resolve(
            url === "/api/bootstrap"
              ? Response.json({ name: "Manpower ERP", stage: "bootstrap" })
              : Response.json(
                  { ...account, csrf_token: "invalid" },
                  { status },
                ),
          ),
        ),
      );
      render(<App />);
      await waitFor(() =>
        expect(screen.getByRole("button", { name: "Sign in" })).toBeEnabled(),
      );
      expect(
        screen.queryByRole("navigation", { name: "Primary navigation" }),
      ).not.toBeInTheDocument();
    },
  );
  it("shows no granted context, no admin authority and honest placeholders", async () => {
    mockApi();
    render(<App />);
    await screen.findByRole("heading", { name: "Workspace overview" });
    expect(screen.getByLabelText("Company and branch context")).toBeDisabled();
    const nav = screen.getByRole("navigation", { name: "Primary navigation" });
    expect(
      within(nav).getByRole("button", { name: "System Administration" }),
    ).toBeDisabled();
    fireEvent.click(
      within(nav).getByRole("button", { name: "General Ledger" }),
    );
    expect(
      screen.getByRole("heading", { name: "General Ledger" }),
    ).toBeVisible();
    expect(screen.getByText("This module is not available yet")).toBeVisible();
    expect(screen.queryByRole("form")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Collapse sidebar" }));
    expect(
      screen.getByRole("button", { name: "Expand sidebar" }),
    ).toHaveAttribute("aria-expanded", "false");
  });

  it("searches static modules and supports an empty result", async () => {
    const request = mockApi();
    render(<App />);
    await screen.findByRole("heading", { name: "Workspace overview" });
    fireEvent.click(
      screen.getByRole("button", { name: "Search workspace modules" }),
    );
    fireEvent.change(screen.getByLabelText("Find a module"), {
      target: { value: "unknown" },
    });
    expect(screen.getByText("No matching modules")).toBeVisible();
    fireEvent.change(screen.getByLabelText("Find a module"), {
      target: { value: "Clients" },
    });
    fireEvent.click(
      within(screen.getByRole("dialog")).getByRole("button", {
        name: /Clients/,
      }),
    );
    expect(screen.getByRole("heading", { name: "Clients" })).toBeVisible();
    expect(request).toHaveBeenCalledTimes(2);
  });

  it("opens mobile navigation without granting scopes", async () => {
    mockApi();
    render(<App />);
    await screen.findByRole("heading", { name: "Workspace overview" });
    fireEvent.click(screen.getByRole("button", { name: "Open navigation" }));
    const nav = screen.getByRole("navigation", {
      name: "Mobile module navigation",
    });
    expect(
      within(nav).getByRole("button", { name: /System Administration/ }),
    ).toBeDisabled();
    fireEvent.click(
      within(nav).getByRole("button", { name: /Service Contracts/ }),
    );
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Service Contracts" }),
    ).toBeVisible();
  });

  it("keeps password change optional and preserves CSRF session transitions", async () => {
    const request = mockApi();
    render(<App />);
    await screen.findByRole("heading", { name: "Workspace overview" });
    expect(screen.queryByLabelText("New password")).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Open my account" }));
    expect(screen.getByLabelText("New password")).toBeVisible();
    fireEvent.click(screen.getAllByRole("button", { name: "Sign out" })[0]);
    await screen.findByRole("form", { name: "Sign in" });
    expect(
      screen.queryByRole("navigation", { name: "Primary navigation" }),
    ).not.toBeInTheDocument();
    expect(request).toHaveBeenLastCalledWith(
      "/api/auth/logout",
      expect.objectContaining({
        headers: { "X-CSRF-Token": account.csrf_token },
        credentials: "same-origin",
      }),
    );
  });

  it("persists only theme preference", async () => {
    localStorage.clear();
    mockApi();
    render(<App />);
    await screen.findByRole("heading", { name: "Workspace overview" });
    fireEvent.click(
      screen.getByRole("button", { name: "Switch to dark theme" }),
    );
    await waitFor(() =>
      expect(document.documentElement).toHaveAttribute("data-theme", "dark"),
    );
    expect(localStorage.getItem("erp-theme")).toBe("dark");
    expect(localStorage.length).toBe(1);
  });

  it("shows failed logout on the current page and retains the session", async () => {
    mockApi(503);
    render(<App />);
    await screen.findByRole("heading", { name: "Workspace overview" });
    fireEvent.click(screen.getByLabelText(/user account menu/i));
    fireEvent.click(screen.getByRole("button", { name: "Sign out" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Unable to sign out",
    );
    expect(
      screen.getByRole("heading", { name: "Workspace overview" }),
    ).toBeVisible();
  });
});
