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
  colorScheme: 'light',
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
      const m = String(rgb).match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?/);
      if (!m) return null;
      let [r,g,b] = [m[1],m[2],m[3]].map(Number).map(v => {
        v /= 255;
        return v <= 0.03928 ? v/12.92 : Math.pow((v+0.055)/1.055, 2.4);
      });
      const a = m[4] != null ? Number(m[4]) : 1;
      // approximate against white for translucent ink-muted on dark; caller uses effectiveBg
      return 0.2126*r + 0.7152*g + 0.0722*b;
    }
    function contrast(fg, bg) {
      const L1 = lum(fg), L2 = lum(bg);
      if (L1 == null || L2 == null) return null;
      const [a,b] = L1 > L2 ? [L1,L2] : [L2,L1];
      return Math.round(((a+0.05)/(b+0.05)) * 100) / 100;
    }
    function walkBg(el) {
      let cur = el;
      while (cur) {
        const bg = getComputedStyle(cur).backgroundColor;
        if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
        cur = cur.parentElement;
      }
      return getComputedStyle(document.body).backgroundColor;
    }
    function sample(sel) {
      const el = document.querySelector(sel);
      if (!el) return { sel, missing: true };
      const cs = getComputedStyle(el);
      const bg = walkBg(el);
      return {
        sel,
        color: cs.color,
        backgroundColor: cs.backgroundColor,
        effectiveBg: bg,
        contrast: contrast(cs.color, bg),
        text: (el.innerText || el.getAttribute('placeholder') || '').slice(0, 60),
        tag: el.tagName,
        className: String(el.className)
      };
    }
    return {
      darkLink: !!document.getElementById('dark-mode-theme'),
      theme: localStorage.getItem('mailcow_theme'),
      body: sample('body'),
      loginCard: sample('.login-card'),
      inputUser: sample('#login_user'),
      fido: sample('#fido2-login'),
      fidoIcon: sample('#fido2-login i'),
      textSecondary: sample('.login-card .text-secondary, .login-card .bi-moon-fill'),
      langSelect: sample('#mailcow-lang, .login-card select, .login-card .text-secondary'),
      forgot: sample('a[href="/reset-password"]'),
      adminLink: sample('a[href="/admin"]'),
      domainAdmin: sample('a[href="/domainadmin"]'),
    };
  });
}

function assertDark(dark) {
  const fails = [];
  const cardBg = dark.loginCard?.backgroundColor || '';
  if (!cardBg.includes('20, 27, 40') && !cardBg.includes('141B28')) {
    // rgb(20, 27, 40) == #141B28 Snow
    fails.push('loginCard not Snow dark: ' + cardBg);
  }
  if ((dark.fido?.color || '').includes('42, 51, 68') || (dark.fido?.contrast != null && dark.fido.contrast < 3)) {
    fails.push('fido dark-on-dark or low contrast: ' + JSON.stringify(dark.fido));
  }
  // FAIL if Bootstrap #555 (#555555 = 85,85,85)
  if ((dark.textSecondary?.color || '').includes('85, 85, 85') || (dark.textSecondary?.color || '') === 'rgb(85, 85, 85)') {
    fails.push('text-secondary still Bootstrap #555: ' + dark.textSecondary.color);
  }
  if (dark.fido?.backgroundColor === dark.loginCard?.backgroundColor && dark.fido?.color === dark.loginCard?.color) {
    // soft check: fido should be Mist distinct from card Snow
    if (dark.fido?.backgroundColor === dark.loginCard?.backgroundColor) {
      fails.push('fido bg same as card (not Mist)');
    }
  }
  return fails;
}

try {
  await page.addInitScript(() => localStorage.setItem('mailcow_theme', 'light'));
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#login_user', { timeout: 30000 });
  await page.waitForTimeout(800);
  await shot('tester-light.png');
  const light = await sampleStyles();
  fs.writeFileSync(`${outDir}/tester-computed-light.json`, JSON.stringify(light, null, 2));
  console.log('LIGHT_OK', light.loginCard?.backgroundColor, light.fido?.color, light.forgot?.color);

  await page.click('#dark-mode-toggle');
  await page.waitForTimeout(1000);
  await shot('tester-dark.png');
  const dark = await sampleStyles();
  fs.writeFileSync(`${outDir}/tester-computed-dark.json`, JSON.stringify(dark, null, 2));
  console.log('DARK', JSON.stringify(dark, null, 2));
  const fails = assertDark(dark);
  if (fails.length) {
    console.error('ASSERT_FAIL', fails);
    process.exitCode = 2;
  } else {
    console.log('ASSERT_PASS');
  }
} catch (e) {
  console.error('ERROR', e);
  await shot('tester-error.png').catch(() => null);
  process.exitCode = 1;
} finally {
  await browser.close();
}
