// export_pdf.js — exports Reveal.js slides to PDF via print-pdf mode
const { chromium } = require('playwright');

async function exportPDF(port, outputPath) {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: ['--no-sandbox', '--disable-gpu']
  });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 960 });

  // Reveal.js print-pdf mode renders all slides in a printable layout
  await page.goto(`http://localhost:${port}/index.html?print-pdf`, {
    waitUntil: 'networkidle',
    timeout: 30000
  });

  // Disable per-fragment pages and hide flip card back faces
  await page.evaluate(() => {
    Reveal.configure({ pdfSeparateFragments: false });
    // Hide all flip card back faces — only front face shows in PDF
    document.querySelectorAll('.flipface.back').forEach(el => {
      el.style.display = 'none';
    });
  });
  await page.waitForTimeout(2000);

  await page.pdf({
    path: outputPath,
    width: '1280px',
    height: '960px',
    printBackground: true,
    margin: { top: 0, right: 0, bottom: 0, left: 0 }
  });

  await browser.close();
  console.log('PDF exported to', outputPath);
}

const [port, outputPath] = process.argv.slice(2);
exportPDF(parseInt(port), outputPath).catch(e => { console.error(e); process.exit(1); });
