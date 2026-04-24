#!/usr/bin/env node
import { chromium } from "playwright-core";

const payload = JSON.parse(process.argv[2] || "{}");

const result = {
  ok: false,
  status: 0,
  finalUrl: payload.url || "",
  title: "",
  html: "",
  error: null,
  stderr: null,
};

const browser = await chromium.launch({
  headless: true,
  executablePath: payload.executablePath,
  args: [
    "--disable-blink-features=AutomationControlled",
    "--no-first-run",
    "--disable-dev-shm-usage",
  ],
});

try {
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1200 },
    locale: "zh-CN",
    userAgent:
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36",
  });

  await context.addInitScript(() => {
    Object.defineProperty(navigator, "webdriver", { get: () => undefined });
  });

  const page = await context.newPage();
  const response = await page.goto(payload.url, {
    waitUntil: payload.waitUntil || "domcontentloaded",
    timeout: payload.timeoutMs || 25000,
  });

  if (payload.waitForSelector) {
    await page.locator(payload.waitForSelector).first().waitFor({
      timeout: payload.timeoutMs || 25000,
    });
  }
  if (payload.postWaitMs) {
    await page.waitForTimeout(payload.postWaitMs);
  }

  result.ok = true;
  result.status = response ? response.status() : 200;
  result.finalUrl = page.url();
  result.title = await page.title();
  result.html = await page.content();

  await context.close();
} catch (error) {
  result.error = String(error);
} finally {
  await browser.close();
}

console.log(JSON.stringify(result));
