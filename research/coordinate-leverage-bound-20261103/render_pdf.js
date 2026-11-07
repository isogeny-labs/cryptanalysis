// Render report.html to report.pdf with the pre-installed Chromium (Playwright).
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const dir = __dirname;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.join(dir, 'report.html'), { waitUntil: 'load' });
  await page.pdf({ path: path.join(dir, 'report.pdf'), format: 'A4', printBackground: true,
                   margin: { top: '18mm', bottom: '18mm', left: '16mm', right: '16mm' } });
  await browser.close();
  console.log('wrote report.pdf');
})();
