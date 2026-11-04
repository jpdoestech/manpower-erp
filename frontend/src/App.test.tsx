import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { App } from "./App";

describe("bootstrap page", () => {
  it("shows loading followed by a connected API", async () => {
    const fetchMock = vi.fn((url: string) =>
      Promise.resolve(
        url === "/api/auth/me"
          ? new Response("{}", { status: 401 })
          : new Response(
              JSON.stringify({ name: "Manpower ERP", stage: "bootstrap" }),
            ),
      ),
    );
    vi.stubGlobal("fetch", fetchMock);
    render(<App />);
    expect(
      screen.getByRole("heading", { level: 1, name: "Manpower ERP" }),
    ).toBeVisible();
    expect(screen.getByRole("status")).toHaveTextContent("Connecting to API…");
    expect(await screen.findByText("API connected")).toBeVisible();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/bootstrap",
      expect.objectContaining({ signal: expect.any(AbortSignal) }),
    );
  });

  it.each([
    () => Promise.reject(new Error("offline")),
    () => Promise.resolve(new Response("{}", { status: 503 })),
    () => Promise.resolve(new Response("{}")),
    () => Promise.resolve(new Response("invalid json")),
  ])("shows a useful failure message", async (fetchResult) => {
    vi.stubGlobal("fetch", vi.fn(fetchResult));
    render(<App />);
    expect(
      await screen.findByText(
        "API unavailable. Check the local API and reload.",
      ),
    ).toBeVisible();
  });
});
