/* Card-local image enlargement. Move the real image/canvas/masks together. */
(function(){
 if(window.nsCloseZoom)window.nsCloseZoom();
 if(window.nsFitCleanup)window.nsFitCleanup();
 var overlay=null,target=null,placeholder=null,oldStyle=null,oldFocus=null,oldOverflow='',scroll=[0,0];
 var frame=null;
 function fitInline(){
  if(overlay)return;
  var units=[],seen=new Set();
  document.querySelectorAll('.ns-card img').forEach(function(img){
   var unit=img.closest('#image-occlusion-container,.ns-picture')||img;
   if(seen.has(unit)||!img.naturalWidth||!img.naturalHeight||!img.getClientRects().length)return;
   seen.add(unit);
   var parent=unit.parentElement,cs=getComputedStyle(parent),width=parent.clientWidth-parseFloat(cs.paddingLeft||0)-parseFloat(cs.paddingRight||0);
   width=Math.min(width,880);
   if(width>0)units.push({unit:unit,width:width,height:width*img.naturalHeight/img.naturalWidth});
  });
  if(!units.length)return;
  var bottom=0;document.querySelectorAll('.ns-card,.ns-local-actions').forEach(function(el){bottom=Math.max(bottom,el.getBoundingClientRect().bottom+window.scrollY)});
  var body=getComputedStyle(document.body),occupied=bottom+parseFloat(body.paddingBottom||0)-units.reduce((n,x)=>n+x.unit.getBoundingClientRect().height,0);
  var budget=Math.max(80,window.innerHeight-occupied-12),natural=units.reduce((n,x)=>n+x.height,0),scale=Math.min(1,budget/natural);
  units.forEach(function(x){var width=x.width*scale;if(Math.abs(x.unit.getBoundingClientRect().width-width)>.25){x.unit.style.width=width+'px';x.unit.style.height='auto'}});
 }
 function schedule(){if(frame!==null)return;frame=requestAnimationFrame(function(){frame=null;fitInline()})}
 window.addEventListener('resize',schedule);document.addEventListener('toggle',schedule,true);
 var observer=typeof ResizeObserver==='function'?new ResizeObserver(schedule):null;
 if(observer)document.querySelectorAll('.ns-card,.ns-local-actions').forEach(el=>observer.observe(el));
 document.querySelectorAll('.ns-card img').forEach(img=>img.addEventListener('load',schedule));
 window.nsFitCleanup=function(){window.removeEventListener('resize',schedule);document.removeEventListener('toggle',schedule,true);if(observer)observer.disconnect();if(frame!==null)cancelAnimationFrame(frame)};
 schedule();
 function nativeAction(action){var b=window.nsImageBridge;if(b&&typeof pycmd==='function')pycmd(b[action])}
 function layout(){
  if(!overlay||!target)return;
  var img=target.matches('img')?target:target.querySelector('img');
  if(!img||!img.naturalWidth||!img.naturalHeight)return;
  var area=overlay.querySelector('.ns-zoom-body'),r=area.getBoundingClientRect();
  var width=Math.max(1,Math.min(r.width,r.height*img.naturalWidth/img.naturalHeight));
  target.style.width=width+'px';target.style.maxWidth='100%';target.style.height='auto';
 }
 function close(){
  if(!overlay)return;
  if(placeholder&&placeholder.isConnected)placeholder.replaceWith(target);
  if(oldStyle===null)target.removeAttribute('style');else target.setAttribute('style',oldStyle);
  target.classList.remove('ns-zoom-target');
  overlay.remove();overlay=null;
  document.body.style.overflow=oldOverflow;
  window.removeEventListener('resize',layout);
  nativeAction('close');
  if(oldFocus&&oldFocus.isConnected)oldFocus.focus();
  schedule();
  requestAnimationFrame(function(){window.scrollTo(scroll[0],scroll[1])});
 }
 window.nsCloseZoom=close;
 function open(unit,e){
  if(overlay)return;
  e.preventDefault();e.stopPropagation();
  target=unit;oldStyle=unit.getAttribute('style');oldFocus=document.activeElement;scroll=[window.scrollX,window.scrollY];
  placeholder=document.createElement('span');unit.before(placeholder);
  overlay=document.createElement('div');overlay.className='ns-zoom';
  overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.setAttribute('aria-label','Bild vergrößern');
  if(unit.closest('.ns-answer'))overlay.dataset.side='answer';
  var bar=document.createElement('div');bar.className='ns-zoom-bar';
  var button=document.createElement('button');button.type='button';button.textContent='Schließen';
  button.setAttribute('aria-label','Bildansicht schließen (Escape)');button.onclick=close;bar.append(button);
  var body=document.createElement('div');body.className='ns-zoom-body';
  unit.classList.add('ns-zoom-target');body.append(unit);overlay.append(bar,body);document.body.append(overlay);
  oldOverflow=document.body.style.overflow;document.body.style.overflow='hidden';
  window.addEventListener('resize',layout);layout();button.focus();nativeAction('open');
  var image=unit.matches('img')?unit:unit.querySelector('img');if(image&&!image.complete)image.addEventListener('load',layout,{once:true});
  requestAnimationFrame(layout);
 }
 document.querySelectorAll('.ns-card img').forEach(function(img){
  var unit=img.closest('#image-occlusion-container,.ns-picture')||img;
  if(unit.dataset.nsZoomBound)return;unit.dataset.nsZoomBound='1';
  unit.classList.add('ns-zoomable');unit.tabIndex=0;unit.setAttribute('role','button');
  unit.setAttribute('aria-label','Bild vergrößern');unit.title='Bild vergrößern';
  unit.addEventListener('click',function(e){open(unit,e)});
  unit.addEventListener('keydown',function(e){if(e.key==='Enter'){open(unit,e)}});
 });
 if(window.nsZoomKeyHandler)document.removeEventListener('keydown',window.nsZoomKeyHandler,true);
 window.nsZoomKeyHandler=function(e){if(overlay&&e.key==='Escape'){e.preventDefault();e.stopImmediatePropagation();close()}};
 document.addEventListener('keydown',window.nsZoomKeyHandler,true);
})();
