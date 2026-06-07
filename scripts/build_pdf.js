// build_pdf.js — assembles slide screenshots into the presentation PDF.
//
// This is the RELIABLE PDF path. Do NOT use Reveal's ?print-pdf (export_pdf.js):
// it emits ~36 duplicate pages because pdfSeparateFragments can't be re-applied
// after load. Building straight from the slide PNGs gives a clean 1-page-per-slide PDF.
//
// Run:  node scripts/build_pdf.js     (from repo root)
const PDFDocument = require('pdfkit');
const fs = require('fs');
const path = require('path');

const ROOT = path.dirname(__dirname);              // repo root (scripts/ is one level down)
const SLIDES_DIR = path.join(ROOT, 'assets', 'slides', 'images');
const OUT = path.join(ROOT, 'assets', 'pdf', 'LLNL_AI_Solutions_Engineer_Presentation.pdf');

const slides = [
  '00_title.png', '01_intro.png', '02a_naive.png', '02b_production.png',
  '03_retrieval.png', '04a_casestudy.png', '04b_arch.png', '05_impact.png',
  '06_tooling.png', '07_close.png',
];

fs.mkdirSync(path.dirname(OUT), { recursive: true });

const doc = new PDFDocument({ autoFirstPage: false, margin: 0 });
doc.pipe(fs.createWriteStream(OUT));
for (const slide of slides) {
  doc.addPage({ size: [1280, 960], margin: 0 });
  doc.image(path.join(SLIDES_DIR, slide), 0, 0, { width: 1280, height: 960 });
}
doc.end();
doc.on('end', () => console.log(`Done — ${slides.length} pages → ${OUT}`));
