import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import {
  Badge,
  ConfirmDialog,
  DataTable,
  Field,
  SearchableDropdown,
  Select,
  Skeleton,
  StatePanel,
  Tabs,
  Toast,
} from "./components";
import { Reference } from "./Reference";

describe("accessible UI primitives", () => {
  it("associates labels, validation and help with native inputs", () => {
    render(
      <>
        <Field label="Name" error="Name is required" />
        <Field label="Date" type="date" hint="Use the effective date" />
        <Select label="Status">
          <option>Draft</option>
        </Select>
        <SearchableDropdown label="Find" options={["Table", "Tabs"]} />
      </>,
    );
    expect(screen.getByLabelText("Name")).toHaveAccessibleDescription(
      "Name is required",
    );
    expect(screen.getByLabelText("Name")).toHaveAttribute(
      "aria-invalid",
      "true",
    );
    expect(screen.getByLabelText("Date")).toHaveAttribute("type", "date");
    expect(screen.getByRole("combobox", { name: "Find" })).toHaveAttribute(
      "list",
    );
    expect(screen.getByRole("combobox", { name: "Status" })).toHaveValue(
      "Draft",
    );
  });

  it("uses headers, caption and a keyboard-scrollable region without fake rows", () => {
    render(
      <DataTable
        caption="Empty records"
        columns={["Name", "Status"]}
        rows={[]}
      />,
    );
    expect(
      screen.getByRole("region", { name: "Empty records" }),
    ).toHaveAttribute("tabindex", "0");
    expect(screen.getAllByRole("columnheader")).toHaveLength(2);
    expect(screen.getByRole("cell")).toHaveTextContent("No records");
  });

  it("supports roving tabs with arrows, Home and End", () => {
    render(
      <Tabs
        label="Examples"
        items={[
          { label: "One", content: "First panel" },
          { label: "Two", content: "Second panel" },
        ]}
      />,
    );
    const one = screen.getByRole("tab", { name: "One" });
    const two = screen.getByRole("tab", { name: "Two" });
    one.focus();
    fireEvent.keyDown(one, { key: "ArrowRight" });
    expect(two).toHaveFocus();
    expect(two).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tabpanel")).toHaveTextContent("Second panel");
    fireEvent.keyDown(two, { key: "Home" });
    expect(one).toHaveFocus();
    fireEvent.keyDown(one, { key: "End" });
    expect(two).toHaveFocus();
    fireEvent.keyDown(two, { key: "ArrowLeft" });
    expect(one).toHaveFocus();
  });

  it("confirmation never acts on cancellation and announces feedback", () => {
    const close = vi.fn();
    const confirm = vi.fn();
    render(
      <>
        <ConfirmDialog
          title="Confirm action"
          confirmLabel="Apply"
          onClose={close}
          onConfirm={confirm}
        >
          Example only
        </ConfirmDialog>
        <Toast message="Example saved" onDismiss={close} />
        <Badge>Draft</Badge>
        <Skeleton />
        <StatePanel kind="unauthorized" title="Access required">
          No scope
        </StatePanel>
      </>,
    );
    fireEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(confirm).not.toHaveBeenCalled();
    expect(close).toHaveBeenCalledOnce();
    fireEvent.click(screen.getByRole("button", { name: "Apply" }));
    expect(confirm).toHaveBeenCalledOnce();
    expect(screen.getByText("Example saved")).toHaveAttribute("role", "status");
    expect(
      screen.getByRole("status", { name: "Loading content" }),
    ).toBeVisible();
  });

  it("validates reference forms without saving business data", () => {
    render(<Reference />);
    fireEvent.click(screen.getByRole("button", { name: "Validate example" }));
    expect(screen.getByLabelText("Example name")).toHaveAccessibleDescription(
      "Enter an example name.",
    );
    fireEvent.change(screen.getByLabelText("Example name"), {
      target: { value: "Synthetic example" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Validate example" }));
    expect(
      screen.getByText("Example validated. No data was saved."),
    ).toBeVisible();
  });
});
