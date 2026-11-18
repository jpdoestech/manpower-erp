import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Companies } from "./Companies";

const company = {
  id: "test-company",
  code: "ALPHA",
  legal_name: "Alpha Company",
  is_active: true,
  version: 1,
};

describe("company registry", () => {
  it("shows an empty authorized scope and supports safe failures", async () => {
    const request = vi
      .fn()
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(new Response(null, { status: 401 }));
    vi.stubGlobal("fetch", request);
    render(<Companies csrfToken={"a".repeat(64)} />);
    await screen.findByText("No authorized companies found");
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await screen.findByText("Companies unavailable");
    expect(screen.queryByText("Alpha Company")).not.toBeInTheDocument();
  });

  it("sends the current version and CSRF when saving and keeps stale edits visible", async () => {
    const request = vi
      .fn()
      .mockResolvedValueOnce(Response.json([company]))
      .mockResolvedValueOnce(new Response(null, { status: 409 }));
    vi.stubGlobal("fetch", request);
    render(<Companies csrfToken={"b".repeat(64)} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Edit Alpha Company" }),
    );
    const dialog = screen.getByRole("dialog");
    fireEvent.change(within(dialog).getByLabelText("Legal company name"), {
      target: { value: "Updated" },
    });
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Save company" }),
    );
    await screen.findByRole("alert");
    expect(request).toHaveBeenLastCalledWith(
      "/api/companies/test-company",
      expect.objectContaining({
        method: "PATCH",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-CSRF-Token": "b".repeat(64),
        },
        body: JSON.stringify({
          legal_name: "Updated",
          is_active: true,
          version: 1,
        }),
      }),
    );
    expect(screen.getByRole("dialog")).toBeVisible();
  });

  it("saves, reloads scoped results and searches with encoded values", async () => {
    const updated = { ...company, legal_name: "Updated", version: 2 };
    const request = vi
      .fn()
      .mockResolvedValueOnce(Response.json([company]))
      .mockResolvedValueOnce(Response.json(updated))
      .mockResolvedValueOnce(Response.json([updated]))
      .mockResolvedValueOnce(Response.json([]));
    vi.stubGlobal("fetch", request);
    render(<Companies csrfToken={"c".repeat(64)} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Edit Alpha Company" }),
    );
    fireEvent.change(screen.getByLabelText("Legal company name"), {
      target: { value: "Updated" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save company" }));
    await screen.findByText("Company saved.");
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    fireEvent.change(screen.getByLabelText("Search companies"), {
      target: { value: "A & B" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));
    await screen.findByText("No authorized companies found");
    expect(request.mock.calls.at(-1)?.[0]).toContain("q=A+%26+B");
  });
});
