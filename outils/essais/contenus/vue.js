const { chromium } = require('/opt/node22/lib/node_modules/playwright');
const sp=process.env.SP;
(async()=>{
  const nav=await chromium.launch({args:['--no-sandbox']});
  const page=await nav.newPage({viewport:{width:1400,height:1200}});
  const err=[]; page.on('pageerror',e=>err.push(String(e).slice(0,120)));
  await page.goto('file://'+sp+'/contenus/ecran.html',{waitUntil:'domcontentloaded'});
  await page.waitForTimeout(250);
  const r=await page.evaluate(()=>({
    zones:[...document.querySelectorAll('.abo-zones .abo-onglet')].map(a=>a.textContent.replace(/\s+/g,' ').trim()),
    barresGabarits:document.querySelectorAll('.abo-onglets--gabarits').length,
    titresZone:[...document.querySelectorAll('.abo-zone-titre')].map(h=>h.textContent.replace(/\s+/g,' ').trim()),
    sections:document.querySelectorAll('section.abo-bloc').length,
    tableaux:document.querySelectorAll('table.abo-table').length,
    lignes:document.querySelectorAll('table.abo-table tbody tr').length,
    nonRange:[...document.querySelectorAll('section.abo-bloc h2')].filter(h=>/Non rangé/.test(h.textContent)).map(h=>h.textContent.replace(/\s+/g,' ').trim()),
  }));
  console.log('onglets de zone   :',r.zones);
  console.log('barres de gabarits:',r.barresGabarits,'(attendu 2)');
  console.log('titres de zone    :',r.titresZone);
  console.log('sections          :',r.sections);
  console.log('tableaux          :',r.tableaux,'· lignes :',r.lignes);
  console.log('« Non rangé »     :',r.nonRange.length?r.nonRange:'aucun');
  console.log('erreurs JS        :',err.length?err:'aucune');
  await page.screenshot({path:sp+'/contenus/ecran.png',fullPage:false});
  await nav.close();
})();
