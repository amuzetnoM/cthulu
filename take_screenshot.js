const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  
  const htmlPath = 'file://' + path.resolve(__dirname, 'system_map.html');
  await page.goto(htmlPath, { waitUntil: 'networkidle0' });
  
  // Wait for D3 to render
  await page.waitForTimeout(3000);
  
  // Take screenshot
  await page.screenshot({ path: 'system_map_screenshot.png', fullPage: false });
  
  console.log('Screenshot saved to system_map_screenshot.png');
  
  await browser.close();
})();
