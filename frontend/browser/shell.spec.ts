import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

// Synthetic API fixtures are confined to this test; runtime has no mock auth path.
async function api(
  page: Page,
  signedIn: boolean,
  companyName = "Synthetic Test Company",
) {
  await page.route("**/api/**", (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === "/api/bootstrap")
      return route.fulfill({
        json: { name: "Manpower ERP", stage: "bootstrap" },
      });
    if (path === "/api/auth/me" && signedIn)
      return route.fulfill({
        json: {
          id: "synthetic-browser-user",
          username: "example-user",
          csrf_token: "a".repeat(64),
        },
      });
    if (path === "/api/companies" && signedIn)
      return route.fulfill({
        json: [
          {
            id: "browser-company",
            code: "DEMO",
            legal_name: companyName,
            is_active: true,
            version: 1,
          },
        ],
      });
    if (signedIn && path.startsWith("/api/companies/browser-company/")) {
      const branch = path.endsWith("/branches");
      const unit = {
        id: branch ? "browser-branch" : "browser-office",
        company_id: "browser-company",
        code: branch ? "BR" : "HO",
        name: branch ? "Synthetic Branch" : "Synthetic Head Office",
        valid_from: "2020-01-01",
        valid_to: null,
        is_active: true,
        version: 1,
        ...(branch
          ? {
              head_office_id: "browser-office",
              head_office_name: "Synthetic Head Office",
            }
          : {}),
      };
      if (route.request().method() === "POST")
        return route.fulfill({
          status: 201,
          json: { ...unit, ...route.request().postDataJSON() },
        });
      return route.fulfill({ json: [unit] });
    }
    return route.fulfill({ status: 401, json: {} });
  });
}
async function noOverflow(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
}
async function accessible(page: Page) {
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .analyze();
  expect(results.violations).toEqual([]);
}

for (const kind of ["head office", "branch"] as const) {
  test(`${kind} hierarchy create form fits every viewport`, async ({
    page,
  }, testInfo) => {
    await api(page, true, `Company${"x".repeat(190)}`);
    await page.goto("/");
    await expect(
      page.getByRole("heading", { name: "Workspace overview" }),
    ).toBeVisible();
    const title = kind === "branch" ? "Branches" : "Head Offices";
    if ((page.viewportSize()?.width ?? 0) <= 600) {
      await page.getByRole("button", { name: "Open navigation" }).click();
      await page
        .getByRole("dialog")
        .getByRole("button", { name: new RegExp(title) })
        .click();
    } else {
      await page
        .getByRole("navigation", { name: "Primary navigation" })
        .getByRole("button", { name: title })
        .click();
    }
    await expect(page.getByLabel("Company", { exact: true })).toBeEnabled();
    await page
      .getByLabel("Company", { exact: true })
      .selectOption("browser-company");
    await expect(
      page.getByRole("button", { name: `Add ${kind}` }),
    ).toBeEnabled();
    await accessible(page);
    await noOverflow(page);
    await page.getByRole("button", { name: `Add ${kind}` }).click();
    const dialog = page.getByRole("dialog", { name: `Add ${kind}` });
    if (kind === "branch") {
      await expect(
        dialog.getByLabel("Head office", { exact: true }),
      ).toBeEnabled();
      await dialog
        .getByLabel("Head office", { exact: true })
        .selectOption("browser-office");
    }
    await dialog.getByLabel("Code", { exact: true }).fill("NEW");
    await dialog.getByLabel("Name", { exact: true }).fill(`New ${kind}`);
    await dialog.getByLabel("Effective from").fill("2020-01-01");
    await accessible(page);
    await noOverflow(page);
    await page.screenshot({
      path: testInfo.outputPath(`hierarchy-${kind.replace(" ", "-")}.png`),
      fullPage: false,
    });
    await dialog.getByRole("button", { name: `Save ${kind}` }).click();
    await expect(
      page.getByText(
        kind === "branch" ? "Branch saved." : "Head office saved.",
      ),
    ).toBeVisible();
    await expect(dialog).toHaveCount(0);
  });
}

test("company registry and edit dialog fit all devices", async ({
  page,
}, testInfo) => {
  await api(page, true);
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Workspace overview" }),
  ).toBeVisible();
  if ((page.viewportSize()?.width ?? 0) <= 600) {
    await page.getByRole("button", { name: "Open navigation" }).click();
    await page
      .getByRole("dialog")
      .getByRole("button", { name: /Company Management/ })
      .click();
  } else {
    await page
      .getByRole("navigation", { name: "Primary navigation" })
      .getByRole("button", { name: "Company Management" })
      .click();
  }
  await expect(
    page.getByRole("heading", { name: "Synthetic Test Company" }),
  ).toBeVisible();
  await accessible(page);
  await noOverflow(page);
  await page
    .getByRole("button", { name: "Edit Synthetic Test Company" })
    .click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await accessible(page);
  await noOverflow(page);
  await page.screenshot({
    path: testInfo.outputPath("company-edit.png"),
    fullPage: false,
  });
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Edit Synthetic Test Company" }),
  ).toBeFocused();
});

test("login fits, labels inputs, hides navigation and supports both themes", async ({
  page,
}, testInfo) => {
  await api(page, false);
  await page.goto("/");
  await expect(
    page.getByRole("button", { name: "Sign in", exact: true }),
  ).toBeEnabled();
  await expect(page.getByRole("navigation")).toHaveCount(0);
  await noOverflow(page);
  await accessible(page);
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await accessible(page);
  await noOverflow(page);
  await page.screenshot({
    path: testInfo.outputPath("login-dark.png"),
    fullPage: false,
  });
});

test("responsive shell, modal keyboard focus, placeholders and account", async ({
  page,
}, testInfo) => {
  await api(page, true);
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Workspace overview" }),
  ).toBeVisible();
  await noOverflow(page);
  await accessible(page);
  await expect(page.getByLabel("Company and branch context")).toBeDisabled();
  const phone = (page.viewportSize()?.width ?? 0) <= 600;
  const search = phone
    ? page
        .getByRole("navigation", { name: "Quick navigation" })
        .getByRole("button", { name: "Search" })
    : page.getByRole("button", { name: "Search workspace modules" });
  if (phone) {
    const rect = await search.boundingBox();
    expect(rect?.height).toBeGreaterThanOrEqual(44);
    await page.getByRole("button", { name: "Open navigation" }).click();
    await expect(
      page.getByRole("dialog", { name: "Workspace navigation" }),
    ).toBeVisible();
    await accessible(page);
    await noOverflow(page);
    await page.keyboard.press("Escape");
    await expect(
      page.getByRole("button", { name: "Open navigation" }),
    ).toBeFocused();
  }
  await search.click();
  const dialog = page.getByRole("dialog", { name: "Search workspace" });
  await expect(dialog).toBeVisible();
  await dialog.getByLabel("Find a module").fill("Clients");
  await page.keyboard.press("Shift+Tab");
  expect(
    await page.evaluate(
      () => document.activeElement?.closest("dialog") !== null,
    ),
  ).toBe(true);
  await page.keyboard.press("Escape");
  await expect(search).toBeFocused();
  await search.click();
  await page.getByLabel("Find a module").fill("Clients");
  await dialog.getByRole("button", { name: /Clients/ }).click();
  await expect(page.getByRole("heading", { name: "Clients" })).toBeVisible();
  await expect(
    page.getByText("This module is not available yet"),
  ).toBeVisible();
  await noOverflow(page);
  await page.getByRole("button", { name: "Back to overview" }).click();
  await expect(page.getByRole("main")).toBeFocused();
  await page.screenshot({
    path: testInfo.outputPath("overview-light.png"),
    fullPage: false,
  });
  await page.getByRole("button", { name: "Switch to dark theme" }).click();
  await accessible(page);
  await noOverflow(page);
  await page.screenshot({
    path: testInfo.outputPath("overview-dark.png"),
    fullPage: false,
  });
  await page.getByRole("button", { name: "Open my account" }).click();
  await expect(page.getByLabel("New password", { exact: true })).toBeVisible();
  await noOverflow(page);
  await accessible(page);
});

test("reference keyboard tabs, validation and confirmation remain accessible", async ({
  page,
}) => {
  await api(page, true);
  await page.goto("/");
  await page.getByRole("button", { name: "Explore design system" }).click();
  await page.getByRole("button", { name: "Validate example" }).click();
  await expect(page.getByLabel("Example name")).toHaveAttribute(
    "aria-invalid",
    "true",
  );
  await noOverflow(page);
  await accessible(page);
  await page.getByRole("button", { name: "Confirmation example" }).click();
  await accessible(page);
  await page.keyboard.press("Escape");
  await expect(
    page.getByRole("button", { name: "Confirmation example" }),
  ).toBeFocused();
  const tab = page.getByRole("tab", { name: "Controls" });
  await tab.focus();
  await page.keyboard.press("End");
  await expect(
    page.getByRole("tab", { name: "Tables & states" }),
  ).toBeFocused();
  await noOverflow(page);
  await accessible(page);
});
