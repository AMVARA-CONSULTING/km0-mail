import { chromium } from 'playwright';
import fs from 'fs';

const outDir = process.env.OUT_DIR || '/out';
const base = process.env.MAIL_BASE || 'https://mail.km0digital.com';

const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const context = await browser.newContext({
  viewport: { width: 1280, height: 900 },
  ignoreHTTPSErrors: true,
  colorScheme: 'dark',
});
const page = await context.newPage();
await page.addInitScript(() => localStorage.removeItem('mailcow_theme'));
await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
await page.waitForSelector('#login_user');
await page.waitForTimeout(1000);
await page.screenshot({ path: `${outDir}/04-prefers-dark.png`, fullPage: false });

const styles = await page.evaluate(() => {
  function sample(sel) {
    const el = document.querySelector(sel);
    if (!el) return { sel, missing: true };
    const cs = getComputedStyle(el);
    return { sel, color: cs.color, backgroundColor: cs.backgroundColor, text: (el.innerText||'').slice(0,40),
      bsCardBg: cs.getPropertyValue('--bs-card-bg'),
      km0Snow: getComputedStyle(document.documentElement).getPropertyValue('--km0-snow').trim(),
      km0Ink: getComputedStyle(document.documentElement).getPropertyValue('--km0-ink').trim(),
      mcSurface: getComputedStyle(document.documentElement).getPropertyValue('--mc-surface').trim(),
    };
  }
  // also sample FIDO icon
  const fidoIcon = document.querySelector('#fido2-login i');
  const fidoIconCs = fidoIcon ? getComputedStyle(fidoIcon) : null;
  return {
    darkLink: !!document.getElementById('dark-mode-theme'),
    theme: localStorage.getItem('mailcow_theme'),
    darkHref: document.getElementById('dark-mode-theme')?.href || null,
    loginCard: sample('.login-card'),
    fido: sample('#fido2-login'),
    fidoIcon: fidoIconCs ? { color: fidoIconCs.color, fill: fidoIconCs.fill } : null,
    body: sample('body'),
    forgot: sample('a[href="/reset-password"]'),
    admin: sample('a[href="/admin"]'),
    // lang toggle button (text-secondary)
    langBtn: sample('.login-card .text-secondary.btn'),
    moonIcon: sample('.login-card .bi-moon-fill'),
  };
});
fs.writeFileSync(`${outDir}/computed-prefers-dark.json`, JSON.stringify(styles, null, 2));
console.log(JSON.stringify(styles, null, 2));
await browser.close();
