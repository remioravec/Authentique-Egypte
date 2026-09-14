(function(){
  var pg=document.querySelector('.pg')||document;
  // Devis : le formulaire compose un message WhatsApp prérempli (aucun envoi ailleurs).
  var f=pg.querySelector('[data-devis]');
  if(f){f.addEventListener('submit',function(e){
    e.preventDefault();
    var m=f.querySelector('select').value||'dates à définir',n=f.querySelector('input[type=number]').value||'?';
    var libre=f.querySelector('input[type=text]'),t=libre?libre.value.trim():'';
    var sejour=f.getAttribute('data-sejour')||document.title,prix=f.getAttribute('data-prix')||'';
    var txt='Bonjour Mélanie, je souhaite un devis pour « '+sejour+' »'+(prix?' (à partir de '+prix+'/pers.)':'')+'.\nPériode : '+m+' · Voyageurs : '+n+(t?'\n'+t:'');
    window.open('https://wa.me/201066619098?text='+encodeURIComponent(txt),'_blank','noopener');
  });}
  // Copier le lien
  var c=pg.querySelector('[data-copier]');
  if(c){c.addEventListener('click',function(){
    var u=c.getAttribute('data-copier');
    (navigator.clipboard?navigator.clipboard.writeText(u):Promise.reject()).then(function(){c.classList.add('ok');c.setAttribute('title','Lien copié');c.setAttribute('aria-label','Lien copié');},function(){window.prompt('Copiez ce lien :',u);});
  });}
  // Carte : un clic sur un point ouvre la journée correspondante.
  pg.querySelectorAll('.carte__pt[data-lieu]').forEach(function(p){
    p.setAttribute('tabindex','0');p.setAttribute('role','button');
    function aller(){
      var l=p.getAttribute('data-lieu').split(/\s+/),cible=null;
      pg.querySelectorAll('.etape[data-lieu]').forEach(function(a){if(!cible&&a.getAttribute('data-lieu').split(/\s+/).some(function(x){return l.indexOf(x)>=0}))cible=a;});
      if(!cible)return;
      var d=cible.closest('details');if(d)d.open=true;
      cible.scrollIntoView({behavior:'smooth',block:'start'});
      cible.classList.add('etape--vise');cible.classList.remove('fin');
      setTimeout(function(){cible.classList.add('fin')},1800);setTimeout(function(){cible.classList.remove('etape--vise','fin')},3200);
    }
    p.addEventListener('click',aller);p.addEventListener('keydown',function(e){if(e.key==='Enter'||e.key===' '){e.preventDefault();aller();}});
  });
  // Navigation par sections : l'onglet suit le défilement.
  var liens=[].slice.call(pg.querySelectorAll('.pg-anc a')),cibles=liens.map(function(a){return document.getElementById(a.getAttribute('href').slice(1))});
  if('IntersectionObserver' in window&&liens.length){
    var actif=function(id){liens.forEach(function(a){a.classList.toggle('vu',a.getAttribute('href')==='#'+id)})};
    var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)actif(e.target.id)})},{rootMargin:'-20% 0px -70% 0px'});
    cibles.forEach(function(t){if(t)io.observe(t)});
  }
})();
