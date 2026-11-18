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
  colorScheme: 'light', // start light; we toggle via UI
});
const page = await context.newPage();
page.setDefaultTimeout(45000);

async function shot(name) {
  const path = `${outDir}/${name}`;
  await page.screenshot({ path, fullPage: false });
  console.log('saved', path, fs.statSync(path).size);
}

function sampleStyles() {
  return page.evaluate(() => {
    function lum(rgb) {
      const m = String(rgb).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
      if (!m) return null;
      const [r,g,b] = [m[1],m[2],m[3]].map(Number).map(v => {
        v /= 255;
        return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
      });
      return 0.2126*r + 0.7152*g + 0.0722*b;
    }
    function contrast(fg, bg) {
      const L1 = lum(fg), L2 = lum(bg);
      if (L1 == null || L2 == null) return null;
      const [a,b] = L1 > L2 ? [L1,L2] : [L2,L1];
      return Math.round(((a+0.05)/(b+0.05)) * 100) / 100;
    }
    function sample(sel) {
      const el = document.querySelector(sel);
      if (!el) return { sel, missing: true };
      const cs = getComputedStyle(el);
      const parent = el.parentElement ? getComputedStyle(el.parentElement) : null;
      const bg = cs.backgroundColor === 'rgba(0, 0, 0, 0)' && parent
        ? parent.backgroundColor : cs.backgroundColor;
      return {
        sel,
        color: cs.color,
        backgroundColor: cs.backgroundColor,
        effectiveBg: bg,
        contrast: contrast(cs.color, bg),
        text: (el.innerText || el.getAttribute('placeholder') || '').slice(0, 60),
        tag: el.tagName,
        className: el.className
      };
    }
    return {
      darkLink: !!document.getElementById('dark-mode-theme'),
      theme: localStorage.getItem('mailcow_theme'),
      body: sample('body'),
      loginCard: sample('.login-card'),
      cardHeader: sample('.login-card .card-header'),
      cardBody: sample('.login-card .card-body'),
      inputUser: sample('#login_user'),
      inputPass: sample('#pass_user'),
      loginBtn: sample('button.btn-success[type="submit"]'),
      fido: sample('#fido2-login'),
      forgot: sample('a[href="/reset-password"]'),
      adminLink: sample('a[href="/admin"]'),
      domainAdmin: sample('a[href="/domainadmin"]'),
      mutedWrap: sample('.login-card .text-muted, p.text-muted'),
      footer: sample('.container.footer, .footer'),
    };
  });
}

try {
  // Force light first
  await page.addInitScript(() => localStorage.setItem('mailcow_theme', 'light'));
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#login_user', { timeout: 30000 });
  await page.waitForTimeout(800);
  await shot('01-login-light.png');
  const light = await sampleStyles();
  fs.writeFileSync(`${outDir}/computed-light.json`, JSON.stringify(light, null, 2));
  console.log('LIGHT', JSON.stringify(light, null, 2));

  // Toggle dark via checkbox
  await page.click('#dark-mode-toggle');
  await page.waitForTimeout(1000);
  await shot('02-login-dark.png');
  const dark = await sampleStyles();
  fs.writeFileSync(`${outDir}/computed-dark.json`, JSON.stringify(dark, null, 2));
  console.log('DARK', JSON.stringify(dark, null, 2));

  // Also force dark via localStorage reload
  await page.evaluate(() => localStorage.setItem('mailcow_theme', 'dark'));
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#login_user');
  await page.waitForTimeout(800);
  await shot('03-login-dark-reload.png');
  const dark2 = await sampleStyles();
  fs.writeFileSync(`${outDir}/computed-dark-reload.json`, JSON.stringify(dark2, null, 2));
  console.log('DARK_RELOAD', JSON.stringify(dark2, null, 2));
} catch (e) {
  console.error('ERROR', e);
  await shot('99-error.png').catch(() => null);
  process.exitCode = 1;
} finally {
  await browser.close();
}
