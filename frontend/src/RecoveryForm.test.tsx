import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { RecoveryForm } from "./RecoveryForm";

describe("password recovery", () => {
  it.each([204, 400, 429, 503])(
    "handles status %s and clears secrets",
    async (status) => {
      const request = vi.fn().mockResolvedValue(new Response(null, { status }));
      vi.stubGlobal("fetch", request);
      render(<RecoveryForm />);
      fireEvent.click(
        screen.getByText("Reset password with an administrator token"),
      );
      fireEvent.change(screen.getByLabelText("Recovery token"), {
        target: { value: "x".repeat(43) },
      });
      fireEvent.change(screen.getByLabelText("Recovery password"), {
        target: { value: "a synthetic recovered password" },
      });
      fireEvent.submit(screen.getByRole("form", { name: "Reset password" }));
      await waitFor(() =>
        expect(screen.getByLabelText("Recovery token")).toHaveValue(""),
      );
      expect(screen.getByLabelText("Recovery password")).toHaveValue("");
      expect(request).toHaveBeenCalledWith(
        "/api/auth/reset-password",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify({
            token: "x".repeat(43),
            new_password: "a synthetic recovered password",
          }),
        }),
      );
      if (status === 204)
        expect(
          screen.getByText("Password reset. Sign in with your new password."),
        ).toBeVisible();
      else
        expect(screen.getByRole("alert")).toHaveTextContent(
          "Unable to reset password",
        );
    },
  );
});
