import AxeBuilder from "@axe-core/playwright";
import { expect, type Page, test } from "@playwright/test";

// Synthetic API fixtures are confined to this test; runtime has no mock auth path.
async function api(page: Page, signedIn: boolean) {
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
