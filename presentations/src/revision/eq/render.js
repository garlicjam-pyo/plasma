// KaTeX → PNG. 40 px 글자 = 30 pt. 사용: NODE_PATH=/opt/npm-tools/node_modules node render.js [이름...]
const fs = require('fs'), path = require('path');
const katex = require('katex');
const { chromium } = require('playwright');
const css = 'file://' + require.resolve('katex/dist/katex.min.css');
const all = JSON.parse(fs.readFileSync('eqs.json', 'utf8'));
const only = process.argv.slice(2);
const eqs = only.length ? all.filter(e => only.includes(e.name)) : all;
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ deviceScaleFactor: 3 });
  const out = fs.existsSync('sizes.json') ? JSON.parse(fs.readFileSync('sizes.json', 'utf8')) : {};
  for (const e of eqs) {
    const html = katex.renderToString(e.src, { displayMode: true, throwOnError: true, strict: false });
    fs.writeFileSync('tmp.html', `<html><head><meta charset="utf-8"><link rel="stylesheet" href="${css}"><style>
body{margin:0;background:transparent;font-size:40px;font-family:'Noto Sans CJK KR',sans-serif}
#box{display:inline-block;padding:4px 6px;color:#1F2340}.katex-display{margin:0}
.katex .text,.katex .mord.text{font-family:'Noto Sans CJK KR',sans-serif}</style></head><body><div id="box">${html}</div></body></html>`);
    await p.goto('file://' + path.resolve('tmp.html'));
    await p.evaluate(() => document.fonts.ready);
    const el = await p.$('#box');
    const bb = await el.boundingBox();
    await el.screenshot({ path: e.name + '.png', omitBackground: true });
    out[e.name] = { w: bb.width, h: bb.height };
  }
  fs.writeFileSync('sizes.json', JSON.stringify(out));
  fs.unlinkSync('tmp.html');
  await b.close();
  console.log('rendered', eqs.length);
})();
