"""Focused real Reviewer geometry check on question/answer and expanded details."""
from pathlib import Path
text=Path(__file__).with_name('test_reviewer.py').read_text(encoding='utf-8')
setup=text.split('    import aqt.webview as webmodule')[0]
png=text[text.index('    import struct,zlib'):text.index('    probes={}; probe_media={}')]
body=r'''
    bridge=__import__('types_test.reviewer_masks',fromlist=['install'])
    sync_ui=__import__('types_test.ui',fromlist=['mw'])
    sync_ui.mw=mw; bridge.install()
    nodes=fixtures.fixtures()[4:]
    nodes.append(fixtures.toggle('Bildfrage',fixtures.image(),fixtures.para('Antwort')))
    for node in nodes: node['_children'].append(fixtures.para('[Header] Zusätzliche Quelle'))
    renderer=fixtures.c.Renderer(lambda *_:(image_png(300,1200),'image/png'))
    values=fixtures.c.parse(nodes,'b'*32,'FitAnswer',renderer)
    before=a.snapshot(mw.col)
    a.apply(mw.col,values,{'b'*32},before,renderer.media,{},a.approval_keys(values,before))
    state=a.snapshot(mw.col)
    for bid,value in values.items():
        kind=value.get('kind','basic'); question(bid)
        for side in ('question','answer'):
            if side=='answer': show_answer()
            for expanded in (False,True):
                js("var h=document.querySelector('.ns-header');if(h)h.open="+str(expanded).lower()+";true")
                sizes=[]
                for width,height in ((520,700),(1000,1000)):
                    mw.web.setFixedSize(width,height); pump(.4)
                    g=js("(function(){var i=document.querySelector('.ns-card img'),b=i.getBoundingClientRect(),f=(document.querySelector('.ns-local-actions')||document.querySelector('.ns-card')).getBoundingClientRect(),h=document.querySelector('.ns-header');return [b.width,b.height,i.naturalWidth/i.naturalHeight,b.bottom,document.querySelector('.ns-local-actions')?f.top:f.bottom,f.bottom,innerHeight,h?h.getBoundingClientRect().top:null]})()")
                    assert abs(g[0]/g[1]-g[2])<.005,(kind,side,g)
                    assert g[3]<=g[4]+1 and g[5]<=g[6]+1,(kind,side,g)
                    if g[7] is not None: assert g[3]<=g[7]+1,(kind,side,g)
                    sizes.append(g)
                assert sizes[1][0]>sizes[0][0],(kind,side,sizes)
            out=scratch/'design-reviewer'/('fit-answer-'+kind+'-'+side+'.png')
            mw.web.grab().save(str(out))
        js("document.querySelector('.ns-zoomable').click();true"); pump(.3)
        assert not mw.isFullScreen() and mw.toolbarWeb.isVisible()
        sizes=[]
        for width,height in ((520,700),(1000,1000)):
            mw.web.setFixedSize(width,height); pump(.3)
            g=js("(function(){var i=document.querySelector('.ns-zoom img'),b=i.getBoundingClientRect(),p=document.querySelector('.ns-zoom').getBoundingClientRect();return [b.width,b.height,i.naturalWidth/i.naturalHeight,p.left,p.right,innerWidth]})()")
            assert abs(g[0]/g[1]-g[2])<.005 and g[3]>0 and g[4]<g[5],g
            sizes.append(g)
        assert sizes[1][0]>sizes[0][0],sizes
        mw.showMaximized(); pump(.2)
        js("document.querySelector('.ns-zoom-bar button').click();true"); pump(.2)
        assert mw.isMaximized() and not mw.isFullScreen()
        assert not js("!!document.querySelector('.ns-zoom')")
        mw.showNormal()
        print('PASS portrait fits question/answer and resizable in-window popup:',kind)
    print('RESPONSIVE ANSWER TEST PASSED')
except Exception:
    traceback.print_exc(); os._exit(1)
finally:
    if aqt.mw.col: aqt.mw.col.close()
os._exit(0)
'''
exec(compile(setup+png+body,__file__,'exec'))

