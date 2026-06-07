// capture_slides.js — screenshot each slide/state using system Chrome
const { chromium } = require('playwright');

async function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

async function captureSlides(port, outputDir) {
  const browser = await chromium.launch({
    headless: true,
    executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    args: ['--no-sandbox', '--disable-gpu']
  });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 1280, height: 960 });

  const BASE = `http://localhost:${port}`;
  await page.goto(BASE + '/index.html', { waitUntil: 'networkidle', timeout: 30000 });
  await sleep(2000);

  async function goToSlide(idx) {
    await page.evaluate((i) => Reveal.slide(i, 0, -1), idx);
    await sleep(600);
  }

  async function advanceAllFragments() {
    for (let i = 0; i < 20; i++) {
      const more = await page.evaluate(() => Reveal.nextFragment());
      await sleep(200);
      if (!more) break;
    }
  }

  async function showCardBack(cardId) {
    await page.evaluate((id) => {
      const card = document.getElementById(id);
      const front = card.querySelector('.flipface.front');
      const back  = card.querySelector('.flipface.back');
      if (front) { front.style.display = 'none'; front.style.transform = ''; }
      if (back)  { back.style.display  = 'block'; back.style.transform  = ''; }
    }, cardId);
    await sleep(400);
  }

  async function shot(name) {
    await page.screenshot({ path: `${outputDir}/${name}`, type: 'png' });
    console.log('captured', name);
  }

  // Title
  await goToSlide(0);
  await shot('00_title.png');

  // Intro — show all fragments
  await goToSlide(1);
  await advanceAllFragments();
  await shot('01_intro.png');

  // Slide 2 front — naive RAG (no fragments needed on the front face)
  await goToSlide(2);
  await shot('02a_naive.png');

  // Slide 2 back — production 3-plane (flip arch-card)
  await goToSlide(2);
  await showCardBack('arch-card');
  await shot('02b_production.png');

  // Slide 3 — retrieval, all fragments
  await goToSlide(3);
  await advanceAllFragments();
  await shot('03_retrieval.png');

  // Slide 4 front — case study use-case
  await goToSlide(4);
  await shot('04a_casestudy.png');

  // Slide 4 back — detailed production architecture
  await goToSlide(4);
  await showCardBack('usecase-card');
  await shot('04b_arch.png');

  // Slide 5 — impact, all fragments
  await goToSlide(5);
  await advanceAllFragments();
  await shot('05_impact.png');

  // Slide 6 — tooling, all fragments
  await goToSlide(6);
  await advanceAllFragments();
  await shot('06_tooling.png');

  // Slide 7 — close
  await goToSlide(7);
  await shot('07_close.png');

  await browser.close();
  console.log('all slides captured');
}

const [port, outputDir] = process.argv.slice(2);
if (!port || !outputDir) {
  console.error('usage: node capture_slides.js <port> <output-dir>');
  process.exit(1);
}
captureSlides(parseInt(port), outputDir).catch(e => { console.error(e); process.exit(1); });
