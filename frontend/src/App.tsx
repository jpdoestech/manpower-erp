import { useEffect, useState } from "react";

export function App() {
  const [status, setStatus] = useState("Connecting to API…");

  useEffect(() => {
    const controller = new AbortController();
    void fetch("/api/bootstrap", { signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("API unavailable");
        const data: unknown = await response.json();
        if (
          typeof data !== "object" ||
          data === null ||
          !("name" in data) ||
          data.name !== "Manpower ERP" ||
          !("stage" in data) ||
          data.stage !== "bootstrap"
        )
          throw new Error("Unexpected API response");
        setStatus("API connected");
      })
      .catch(() => {
        if (!controller.signal.aborted)
          setStatus("API unavailable. Check the local API and reload.");
      });
    return () => controller.abort();
  }, []);

  return (
    <main>
      <header>
        <span className="mark" aria-hidden="true">
          M.
        </span>
        <span>PHILIPPINE MANPOWER SYSTEMS</span>
      </header>
      <section aria-labelledby="title">
        <p className="eyebrow">P0-01 / DEVELOPMENT</p>
        <h1 id="title">Manpower ERP</h1>
        <p className="intro">The foundation for your operations.</p>
        <p role="status">{status}</p>
        <p className="note">
          Local development bootstrap. Business modules are not available yet.
        </p>
      </section>
      <footer>
        LOCAL WORKSPACE <span>01 / FOUNDATION</span>
      </footer>
    </main>
  );
}
