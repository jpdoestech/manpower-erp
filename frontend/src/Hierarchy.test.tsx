import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { Hierarchy } from "./Hierarchy";

const company = {
  id: "company-a",
  code: "ALPHA",
  legal_name: "Alpha Company",
  is_active: true,
};
const other = {
  ...company,
  id: "company-b",
  code: "BRAVO",
  legal_name: "Bravo Company",
};
const office = {
  id: "office-a",
  company_id: company.id,
  code: "HO",
  name: "Manila Office",
  valid_from: "2020-01-01",
  valid_to: null,
  is_active: true,
  version: 1,
};
const branch = {
  ...office,
  id: "branch-a",
  code: "BR",
  name: "Makati Branch",
  head_office_id: office.id,
  head_office_name: office.name,
};

async function selectCompany() {
  await waitFor(() => expect(screen.getByLabelText("Company")).toBeEnabled());
  fireEvent.change(screen.getByLabelText("Company"), {
    target: { value: company.id },
  });
}

describe("head offices and branches", () => {
  it("keeps old company results hidden when company selection changes", async () => {
    let finish: ((value: Response) => void) | undefined;
    const request = vi.fn((url: string) => {
      if (url.startsWith("/api/companies?"))
        return Promise.resolve(Response.json([company, other]));
      if (url.includes(company.id))
        return new Promise<Response>((resolve) => {
          finish = resolve;
        });
      return Promise.resolve(
        Response.json([
          { ...office, company_id: other.id, name: "Bravo Office" },
        ]),
      );
    });
    vi.stubGlobal("fetch", request);
    render(<Hierarchy kind="head-offices" csrfToken={"a".repeat(64)} />);
    expect(
      screen.getByRole("button", { name: "Add head office" }),
    ).toBeDisabled();
    await selectCompany();
    await waitFor(() => expect(finish).toBeDefined());
    fireEvent.change(screen.getByLabelText("Company"), {
      target: { value: other.id },
    });
    await screen.findByRole("heading", { name: "Bravo Office" });
    finish?.(Response.json([office]));
    await waitFor(() =>
      expect(
        screen.queryByRole("heading", { name: office.name }),
      ).not.toBeInTheDocument(),
    );
    expect(request.mock.calls[0]?.[0]).toContain("hierarchy=true");
  });

  it("creates a head office with the authenticated CSRF and scoped path", async () => {
    const request = vi.fn((url: string, options?: RequestInit) =>
      Promise.resolve(
        url.startsWith("/api/companies?")
          ? Response.json([company])
          : options?.method === "POST"
            ? Response.json(office, { status: 201 })
            : Response.json([]),
      ),
    );
    vi.stubGlobal("fetch", request);
    render(<Hierarchy kind="head-offices" csrfToken={"b".repeat(64)} />);
    await selectCompany();
    fireEvent.click(
      await screen.findByRole("button", { name: "Add head office" }),
    );
    fireEvent.change(screen.getByLabelText("Code"), {
      target: { value: "HO" },
    });
    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: office.name },
    });
    fireEvent.change(screen.getByLabelText("Effective from"), {
      target: { value: "2020-01-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save head office" }));
    await screen.findByText("Head office saved.");
    const mutation = request.mock.calls.find(
      (call) => call[1]?.method === "POST",
    );
    expect(mutation?.[0]).toBe("/api/companies/company-a/head-offices");
    expect(mutation?.[1]?.headers).toEqual({
      "Content-Type": "application/json",
      "X-CSRF-Token": "b".repeat(64),
    });
    expect(JSON.parse(String(mutation?.[1]?.body))).toEqual({
      code: "HO",
      name: office.name,
      valid_from: "2020-01-01",
      valid_to: null,
      is_active: true,
    });
  });

  it("selects a head office inside the selected company when adding a branch", async () => {
    const request = vi.fn((url: string, options?: RequestInit) =>
      Promise.resolve(
        url.startsWith("/api/companies?")
          ? Response.json([company])
          : options?.method === "POST"
            ? Response.json(branch, { status: 201 })
            : url.includes("head-offices")
              ? Response.json([office])
              : Response.json([]),
      ),
    );
    vi.stubGlobal("fetch", request);
    render(<Hierarchy kind="branches" csrfToken={"c".repeat(64)} />);
    await selectCompany();
    await waitFor(() =>
      expect(screen.getByRole("button", { name: "Add branch" })).toBeEnabled(),
    );
    fireEvent.click(screen.getByRole("button", { name: "Add branch" }));
    await waitFor(() =>
      expect(screen.getByLabelText("Head office")).toBeEnabled(),
    );
    expect(screen.getByRole("button", { name: "Save branch" })).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Head office"), {
      target: { value: office.id },
    });
    fireEvent.change(screen.getByLabelText("Code"), {
      target: { value: "BR" },
    });
    fireEvent.change(screen.getByLabelText("Name"), {
      target: { value: branch.name },
    });
    fireEvent.change(screen.getByLabelText("Effective from"), {
      target: { value: "2020-01-01" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Save branch" }));
    await screen.findByText("Branch saved.");
    const mutation = request.mock.calls.find(
      (call) => call[1]?.method === "POST",
    );
    expect(JSON.parse(String(mutation?.[1]?.body)).head_office_id).toBe(
      office.id,
    );
  });

  it("preserves edits on conflict and prevents changing immutable relationship fields", async () => {
    const request = vi.fn((url: string, options?: RequestInit) =>
      Promise.resolve(
        url.startsWith("/api/companies?")
          ? Response.json([company])
          : options?.method === "PATCH"
            ? new Response(null, { status: 409 })
            : Response.json([branch]),
      ),
    );
    vi.stubGlobal("fetch", request);
    render(<Hierarchy kind="branches" csrfToken={"d".repeat(64)} />);
    await selectCompany();
    fireEvent.click(
      await screen.findByRole("button", { name: `Edit ${branch.name}` }),
    );
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByLabelText("Effective from")).toBeDisabled();
    expect(
      within(dialog).queryByLabelText("Head office"),
    ).not.toBeInTheDocument();
    fireEvent.click(
      within(dialog).getByRole("button", { name: "Save branch" }),
    );
    await screen.findByRole("alert");
    const mutation = request.mock.calls.find(
      (call) => call[1]?.method === "PATCH",
    );
    expect(JSON.parse(String(mutation?.[1]?.body))).toEqual({
      name: branch.name,
      valid_to: null,
      is_active: true,
      version: 1,
    });
    expect(screen.getByRole("dialog")).toBeVisible();
  });

  it("fails closed for wrong-company data and failed capability checks", async () => {
    const request = vi.fn((url: string) =>
      Promise.resolve(
        url.startsWith("/api/companies?")
          ? Response.json([company])
          : Response.json([{ ...office, company_id: other.id }]),
      ),
    );
    vi.stubGlobal("fetch", request);
    render(<Hierarchy kind="head-offices" csrfToken="csrf" />);
    await selectCompany();
    await screen.findByText("Records unavailable");
    expect(
      screen.queryByRole("heading", { name: office.name }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Add head office" }),
    ).toBeDisabled();
  });
});
