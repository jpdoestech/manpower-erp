import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./browser",
  fullyParallel: true,
  workers: 2,
  retries: 0,
  use: {
    baseURL: "http://127.0.0.1:5174",
    browserName: "chromium",
    trace: "retain-on-failure",
  },
  webServer: {
    command: "node node_modules/vite/bin/vite.js --host 127.0.0.1 --port 5174",
    url: "http://127.0.0.1:5174",
    reuseExistingServer: false,
  },
  projects: [
    {
      name: "phone-narrow",
      use: {
        viewport: { width: 320, height: 740 },
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: "phone-small",
      use: {
        viewport: { width: 360, height: 800 },
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: "phone",
      use: {
        viewport: { width: 390, height: 844 },
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: "tablet",
      use: { viewport: { width: 768, height: 1024 }, hasTouch: true },
    },
    { name: "laptop", use: { viewport: { width: 1366, height: 768 } } },
    { name: "desktop", use: { viewport: { width: 1920, height: 1080 } } },
    {
      name: "phone-landscape",
      use: {
        viewport: { width: 844, height: 390 },
        isMobile: true,
        hasTouch: true,
      },
    },
    {
      name: "tablet-wide",
      use: { viewport: { width: 1024, height: 768 }, hasTouch: true },
    },
    { name: "desktop-wide", use: { viewport: { width: 2560, height: 1440 } } },
  ],
});
