import { useState } from "react";
import {
  Badge,
  Button,
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

export function Reference() {
  const [confirm, setConfirm] = useState(false);
  const [toast, setToast] = useState("");
  const [name, setName] = useState("");
  const [submitted, setSubmitted] = useState(false);
  return (
    <>
      <div className="page-heading">
        <div>
          <p className="eyebrow">UI-001 / INTERFACE FOUNDATION</p>
          <h1>Design system</h1>
          <p className="muted">
            Reusable patterns. These examples do not create ERP records.
          </p>
        </div>
        <Badge>UI reference</Badge>
      </div>
      <Tabs
        label="Component reference"
        items={[
          {
            label: "Controls",
            content: (
              <div className="reference-grid">
                <section className="card">
                  <h2>Form controls</h2>
                  <form
                    onSubmit={(event) => {
                      event.preventDefault();
                      setSubmitted(true);
                      if (name.trim())
                        setToast("Example validated. No data was saved.");
                    }}
                    noValidate
                  >
                    <Field
                      label="Example name"
                      value={name}
                      onChange={(event) => setName(event.target.value)}
                      required
                      error={
                        submitted && !name.trim()
                          ? "Enter an example name."
                          : undefined
                      }
                      hint="Required. UI demonstration only."
                    />
                    <Select label="Example status">
                      <option>Draft</option>
                      <option>In review</option>
                    </Select>
                    <SearchableDropdown
                      label="Find a component"
                      options={["Button", "Dialog", "Table", "Tabs"]}
                      hint="Type to filter native suggestions."
                    />
                    <Field label="Example date" type="date" />
                    <Button type="submit">Validate example</Button>
                  </form>
                </section>
                <section className="card">
                  <h2>Actions & feedback</h2>
                  <div className="actions">
                    <Button
                      onClick={() =>
                        setToast("Example action completed. No data changed.")
                      }
                    >
                      Primary action
                    </Button>
                    <Button
                      variant="secondary"
                      onClick={() => setConfirm(true)}
                    >
                      Confirmation example
                    </Button>
                    <Button disabled>Unavailable</Button>
                  </div>
                  <h3>Status indicators</h3>
                  <div className="actions">
                    <Badge>Draft</Badge>
                    <Badge tone="warning">In review</Badge>
                    <Badge tone="success">Approved example</Badge>
                    <Badge tone="danger">Rejected example</Badge>
                  </div>
                  <p className="muted">
                    Status examples are presentation only, never approval
                    evidence.
                  </p>
                  <h3>Loading skeleton</h3>
                  <Skeleton />
                </section>
              </div>
            ),
          },
          {
            label: "Tables & states",
            content: (
              <div className="stack">
                <section className="card">
                  <h2>Empty data table</h2>
                  <DataTable
                    caption="Example records — no data source"
                    columns={["Reference", "Description", "Status", "Updated"]}
                    rows={[]}
                  />
                </section>
                <div className="reference-grid">
                  <StatePanel title="Nothing here yet">
                    Explain the next available step without inventing records.
                  </StatePanel>
                  <StatePanel kind="unauthorized" title="Access required">
                    Ask an authorized administrator to review your scope.
                  </StatePanel>
                  <StatePanel
                    kind="error"
                    title="Unable to load this example"
                    action={
                      <Button
                        variant="secondary"
                        onClick={() =>
                          setToast("Retry example only. No API request sent.")
                        }
                      >
                        Retry example
                      </Button>
                    }
                  >
                    Show a safe message and a clear retry action.
                  </StatePanel>
                </div>
              </div>
            ),
          },
        ]}
      />
      {confirm && (
        <ConfirmDialog
          title="Confirm example action"
          confirmLabel="Confirm example"
          onClose={() => setConfirm(false)}
          onConfirm={() => {
            setConfirm(false);
            setToast("Example confirmed. No records changed.");
          }}
        >
          Real destructive actions must describe their impact and require server
          authorization.
        </ConfirmDialog>
      )}
      {toast && <Toast message={toast} onDismiss={() => setToast("")} />}
    </>
  );
}
