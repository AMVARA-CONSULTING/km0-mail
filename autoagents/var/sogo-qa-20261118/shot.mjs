import { chromium } from 'playwright';
import fs from 'fs';

const outDir = process.env.OUT_DIR || '/out';
const user = process.env.MAIL_USER;
const pass = process.env.MAIL_PASS;
const base = process.env.MAIL_BASE || 'https://mail.km0digital.com';

const browser = await chromium.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const context = await browser.newContext({
  viewport: { width: 1440, height: 900 },
  ignoreHTTPSErrors: true
});
const page = await context.newPage();
page.setDefaultTimeout(60000);

async function shot(name) {
  const path = `${outDir}/${name}`;
  await page.screenshot({ path, fullPage: false });
  console.log('saved', path, fs.statSync(path).size);
}

try {
  console.log('goto login');
  await page.goto(base + '/', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#login_user', { timeout: 30000 });
  await page.fill('#login_user', user);
  await page.fill('#pass_user', pass);
  await Promise.all([
    page.waitForNavigation({ waitUntil: 'domcontentloaded', timeout: 60000 }).catch(() => null),
    page.click('button[type="submit"].btn-success')
  ]);
  await page.waitForTimeout(3000);
  console.log('after login url', page.url());
  await shot('01-after-login.png');

  // Navigate to SOGo webmail
  const sogoCandidates = [
    base + '/SOGo/',
    base + '/SOGo/so/' + encodeURIComponent(user) + '/Mail',
    base + '/SOGo/so/' + encodeURIComponent(user) + '/Mail/view'
  ];
  let opened = false;
  for (const url of sogoCandidates) {
    console.log('try', url);
    const resp = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    console.log('status', resp && resp.status(), 'url', page.url());
    await page.waitForTimeout(5000);
    // Wait for sidenav / mailbox UI
    const hasUi = await page.locator('md-sidenav, #messagesList, .sg-mailbox-list-item').count();
    console.log('ui count', hasUi);
    if (hasUi > 0 || page.url().includes('/SOGo')) {
      opened = true;
      break;
    }
  }
  await shot('02-sogo-mail.png');

  // Click Inbox if present
  const inbox = page.locator('text=/^(Inbox|Bandeja de entrada)$/i').first();
  if (await inbox.count()) {
    await inbox.click().catch(() => null);
    await page.waitForTimeout(3000);
  }
  await shot('03-inbox.png');

  // Ensure no message selected / empty preview — try deselect
  await page.keyboard.press('Escape').catch(() => null);
  await page.waitForTimeout(1000);
  await shot('04-empty-preview.png');

  // Sent / Drafts
  for (const label of ['Sent', 'Enviados', 'Drafts', 'Borradores']) {
    const loc = page.locator(`text=/^${label}$/i`).first();
    if (await loc.count()) {
      await loc.click().catch(() => null);
      await page.waitForTimeout(2500);
      await shot(`05-${label.toLowerCase()}.png`);
      break;
    }
  }

  // Capture computed styles for key nodes
  const styles = await page.evaluate(() => {
    function sample(sel) {
      const el = document.querySelector(sel);
      if (!el) return { sel, missing: true };
      const cs = getComputedStyle(el);
      return {
        sel,
        color: cs.color,
        backgroundColor: cs.backgroundColor,
        text: (el.innerText || '').slice(0, 80)
      };
    }
    return {
      sidenav: sample('md-sidenav.md-sidenav-left'),
      folderItem: sample('md-sidenav .sg-mailbox-list-item, md-sidenav md-list-item'),
      folderName: sample('md-sidenav .sg-item-name, md-sidenav .sg-no-wrap'),
      messagesList: sample('#messagesList, .view-list'),
      emptyTitle: sample('md-content .sg-md-title, .sg-md-title'),
      contrastStyle: !!document.getElementById('km0-sogo-contrast'),
      url: location.href,
      title: document.title
    };
  });
  fs.writeFileSync(`${outDir}/computed-styles.json`, JSON.stringify(styles, null, 2));
  console.log('styles', JSON.stringify(styles, null, 2));
} catch (e) {
  console.error('ERROR', e);
  await shot('99-error.png').catch(() => null);
  process.exitCode = 1;
} finally {
  await browser.close();
}
