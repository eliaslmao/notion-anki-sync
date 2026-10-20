"""One adaptive presentation layer for all managed card models."""
import re
from pathlib import Path

STYLE_START = '/* ns-design-v1:start */'
STYLE_END = '/* ns-design-v1:end */'
WRAP_MARK = '<!-- ns-card-layout-v1 -->'
CONTROL_SCRIPT = r'''<!-- ns-sequence-controls-v1 --><script>(function(){
if(window.nsSequenceKeyHandler)document.removeEventListener('keydown',window.nsSequenceKeyHandler,true);
document.querySelectorAll('.ns-widget').forEach(function(w){
 var order=JSON.parse(w.dataset.order),masks=Array.from(w.querySelectorAll('.ns-mask')),
 next=w.querySelector('.ns-next'),reset=w.querySelector('.ns-reset'),answer=!!w.closest('.ns-answer');
 masks.forEach(function(m){m.tabIndex=-1;m.setAttribute('aria-hidden','true');m.textContent=String(order.indexOf(Number(m.dataset.mask))+1)});
 function remaining(){return masks.filter(m=>m.style.visibility!=='hidden').length}
 function status(){if(next){next.disabled=remaining()===0;next.textContent=remaining()?'Weiter aufdecken':'Alles aufgedeckt';next.setAttribute('aria-label','Nächste Maske aufdecken')}}
 function step(notify){if(!w.isConnected||answer)return;var id=order.find(id=>masks.some(m=>Number(m.dataset.mask)===id&&m.style.visibility!=='hidden'));var m=masks.find(m=>Number(m.dataset.mask)===id);if(m)m.style.visibility='hidden';status();if(m&&remaining()===0&&notify!==false&&typeof pycmd==='function')pycmd('ans')}
 window.nsSequence={ready:()=>w.isConnected&&!answer,remaining:remaining,step:step};
 if(next)next.onclick=function(e){e.preventDefault();e.stopPropagation();step()};
 if(reset)reset.onclick=function(e){e.preventDefault();e.stopPropagation();masks.forEach(m=>m.style.visibility='visible');status()};
 status();
});
window.nsSequenceKeyHandler=function(e){var s=window.nsSequence;if(!s||!s.ready()||![' ','Enter'].includes(e.key))return;
 if(e.target.closest('input,textarea,select,a,summary')||e.target.closest('button:not(.ns-next)'))return;
 e.preventDefault();e.stopImmediatePropagation();if(e.repeat)return;
 if(s.remaining()>0)s.step();else if(typeof pycmd==='function')pycmd('ans');
};
document.addEventListener('keydown',window.nsSequenceKeyHandler,true);
})();</script>'''
INTERACTION_SCRIPT = '<!-- ns-image-interactions-v1 --><script>'+Path(__file__).with_name('card_interactions.js').read_text(encoding='utf-8')+'</script>'

CARD_CSS = r'''
:root {
  --ns-bg:#f5f5f7; --ns-surface:#ffffff; --ns-text:#1d1d1f;
  --ns-secondary:#5c5c63; --ns-line:#d2d2d7; --ns-accent:#0066cc;
  --ns-control:#ffffff; --ns-hover:#e8f1fc; --ns-focus:#0066cc;
  --ns-success:#176b3b; --ns-error:#b42318;
  --ns-mask:#ffcc66; --ns-mask-inactive:#f2e3b4; --ns-mask-line:#855600;
  --ns-space:1rem; --ns-radius:10px;
}
.nightMode, .night_mode {
  color-scheme:dark; --ns-bg:#1c1c1e; --ns-surface:#2c2c2e;
  --ns-text:#f5f5f7; --ns-secondary:#b5b5bd; --ns-line:#48484a;
  --ns-accent:#8ac1ff; --ns-control:#2c2c2e; --ns-hover:#263d56; --ns-focus:#8ac1ff;
  --ns-success:#81d7a0; --ns-error:#ff9c94;
}
.card, .card.nightMode, .card.night_mode {
  box-sizing:border-box; margin:0; padding:24px;
  padding:clamp(20px,5vw,48px); background:var(--ns-bg); color:var(--ns-text);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Helvetica Neue",Arial,sans-serif;
  font-size:20px; line-height:1.6; text-align:left; overflow-wrap:anywhere;
}
.card *, .card *::before, .card *::after { box-sizing:border-box; }
.ns-card, .ns-local-actions { width:100%; max-width:44rem; margin-inline:auto; }
.ns-card .ns-card { margin:0; }
.ns-card p { margin:.65em 0; }
.ns-card ul, .ns-card ol { padding-inline-start:1.5em; }
.ns-card li + li { margin-top:.35em; }
.ns-card img { max-width:100%; max-height:none!important; height:auto!important; object-fit:contain; }
.ns-card table { display:block; max-width:100%; overflow-x:auto; border-collapse:collapse; }
.ns-card td, .ns-card th { padding:.5em .75em; border:1px solid var(--ns-line); }
.ns-card blockquote { margin:1em 0; padding-inline-start:1em; border-inline-start:3px solid var(--ns-line); color:var(--ns-secondary); }
.ns-card code { font: .9em ui-monospace,Consolas,monospace; }
.ns-task { font-size:1.1em; font-weight:600; line-height:1.45; margin-bottom:1.25em; }
.ns-card a { color:var(--ns-accent); text-underline-offset:.16em; }
.ns-card hr, #answer { border:0; border-top:1px solid var(--ns-line); margin:1.75em 0; }
.ns-card .cloze { color:var(--ns-accent); font-weight:600; }
.ns-card input[type=text], .ns-card #typeans, .ns-inline-input {
  color:var(--ns-text); background:var(--ns-control); border:1px solid var(--ns-line);
  border-radius:var(--ns-radius); padding:.45em .65em; font:inherit; min-height:44px;
  max-width:100%;
}
.ns-inline-input { display:inline-block; width:9em; min-width:3em; vertical-align:baseline; }
.ns-card .typeGood { color:var(--ns-success); background:transparent; }
.ns-card .typeBad, .ns-card .typeMissed { color:var(--ns-error); background:transparent; }
.ns-inline-feedback { display:inline-block; font-size:.8em; margin-inline:.3em; padding:.15em .45em;
  border:1px solid var(--ns-line); border-radius:6px; background:var(--ns-surface); line-height:1.35; }
.ns-inline-ok { color:var(--ns-success); }
.ns-inline-wrong { color:var(--ns-error); }
.ns-card button:not(.ns-mask), .ns-local-actions button, .ns-header summary {
  min-width:44px; min-height:44px; font:inherit; font-size:.85em;
  border-radius:var(--ns-radius); padding:10px 16px; line-height:1.4;
  background:var(--ns-control); color:var(--ns-text); border:1px solid var(--ns-line); cursor:pointer;
}
.ns-card button:not(.ns-mask):hover, .ns-local-actions button:hover, .ns-header summary:hover { background:var(--ns-hover); }
.ns-card button:not(.ns-mask):active, .ns-local-actions button:active { border-color:var(--ns-accent); }
.ns-card button:disabled { cursor:default; color:var(--ns-secondary); background:var(--ns-bg); }
.ns-card button:focus-visible, .ns-local-actions button:focus-visible, .ns-card input:focus-visible,
.ns-card a:focus-visible, .ns-header summary:focus-visible { outline:3px solid var(--ns-focus); outline-offset:3px; }
.ns-header { margin-top:clamp(3em,8vw,4.5em); padding-top:1em; border-top:1px solid var(--ns-line); font-size:.85em; color:var(--ns-secondary); }
.ns-header summary { display:list-item; width:fit-content; max-width:100%; color:var(--ns-text); }
.ns-header>div { margin-top:1em; }
.ns-local-actions { margin-top:3em; padding-top:1em; border-top:1px solid var(--ns-line); }
.ns-card:has(.ns-header) + .ns-local-actions { border-top:0; margin-top:1.5em; padding-top:0; }
.card:has(.ns-card img) { padding:clamp(20px,3vw,32px); }
.ns-card:has(img) .ns-header { margin-top:2em; }
.ns-card:has(img) + .ns-local-actions { margin-top:1.5em; }
.ns-widget { margin:1em 0; }
.ns-picture { width:100%; max-width:44rem; }
.ns-picture img { width:100%; }
.ns-mask { background:var(--ns-mask); color:#27200b; border:2px solid var(--ns-mask-line); font:600 .75em/1 Arial,sans-serif; }
.ns-next { margin:.5em .5em .5em 0; }
#image-occlusion-canvas {
  --inactive-shape-color:var(--ns-mask-inactive); --active-shape-color:var(--ns-mask);
  --inactive-shape-border:1px #855600; --active-shape-border:2px #855600;
  --highlight-shape-color:#ffcc6600; --highlight-shape-border:2px #855600;
}
#image-occlusion-container { width:100%; max-width:44rem; }
#image-occlusion-container img, #image-occlusion-canvas { max-height:none!important; height:auto!important; }
.ns-zoomable { cursor:zoom-in; }
.ns-zoomable:focus-visible { outline:3px solid var(--ns-focus); outline-offset:3px; }
.ns-zoom { position:fixed; inset:12px; z-index:2147483647; display:flex; flex-direction:column;
  background:var(--ns-surface); color:var(--ns-text); padding:16px; gap:12px;
  border:1px solid var(--ns-line); border-radius:14px; box-shadow:0 8px 32px #0005; }
.ns-zoom-bar { display:flex; justify-content:flex-end; flex:none; }
.ns-zoom-bar button { min-height:44px; min-width:44px; padding:10px 16px; font:inherit;
  border:1px solid var(--ns-line); border-radius:10px; background:var(--ns-control); color:var(--ns-text); cursor:pointer; }
.ns-zoom-bar button:focus-visible { outline:3px solid var(--ns-focus); outline-offset:2px; }
.ns-zoom-body { min-height:0; min-width:0; flex:1; display:flex; align-items:center; justify-content:center; }
.ns-zoom .ns-zoom-target { flex:none; margin:0; }
.ns-zoom img { display:block; max-height:none!important; height:auto!important; max-width:100%; object-fit:contain; }
.ns-zoom .ns-picture img { width:100%; }
.ns-zoom canvas { max-width:100%; max-height:none!important; height:auto!important; }
.ns-zoom[data-side="answer"] .ns-mask { visibility:hidden!important; }
@media (prefers-reduced-motion:reduce) { .ns-card *, .ns-local-actions * { animation:none!important; transition:none!important; scroll-behavior:auto!important; } }
@media (forced-colors:active) {
  .card { --ns-bg:Canvas; --ns-surface:Canvas; --ns-text:CanvasText; --ns-secondary:CanvasText;
    --ns-line:CanvasText; --ns-accent:LinkText; --ns-control:ButtonFace; --ns-focus:Highlight; --ns-hover:ButtonFace; }
}
'''


def apply_style(model,kind):
    css = re.sub(re.escape(STYLE_START)+r'.*?'+re.escape(STYLE_END),'',model['css'],flags=re.S)
    model['css'] = css+STYLE_START+CARD_CSS+STYLE_END
    for key in ('qfmt','afmt'):
        value = model['tmpls'][0][key]
        if kind=='sequence':
            value = re.sub(r'<!-- ns-sequence-controls-v1 -->.*?</script>','',value,flags=re.S)
            value = value[:-6]+CONTROL_SCRIPT+'</div>' if WRAP_MARK in value and value.endswith('</div>') else value+CONTROL_SCRIPT
        value = re.sub(r'<!-- ns-image-interactions-v1 -->.*?</script>','',value,flags=re.S)
        value = value[:-6]+INTERACTION_SCRIPT+'</div>' if WRAP_MARK in value and value.endswith('</div>') else value+INTERACTION_SCRIPT
        if WRAP_MARK in value:
            model['tmpls'][0][key] = value
            continue
        if kind in ('image','images'):
            value = value.replace('{{#Front}}<div>{{Front}}</div>{{/Front}}','{{#Front}}<div class="ns-task">{{Front}}</div>{{/Front}}')
        elif kind in ('input','sequence'):
            value = value.replace('{{Front}}<br>','<div class="ns-task">{{Front}}</div>')
        model['tmpls'][0][key] = WRAP_MARK+'<div class="ns-card ns-card-'+kind+'">'+value+'</div>'
