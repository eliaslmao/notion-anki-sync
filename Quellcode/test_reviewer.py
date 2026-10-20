"""Actual AnkiQt Reviewer + Chromium test in a brand-new synthetic profile."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'
os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--no-sandbox --disable-gpu'
os.environ['ANKI_SOFTWAREOPENGL'] = '1'
import importlib.util
import pathlib
import sys
import tempfile
import time
import traceback
import anki.lang
from aqt.profiles import ProfileManager

source = pathlib.Path(__file__).resolve().parent
scratch = source.parent/'work'
scratch.mkdir(exist_ok=True)
base = pathlib.Path(tempfile.mkdtemp(prefix='anki-reviewer-',dir=scratch))
anki.lang.set_lang('en')
pm = ProfileManager(base)
pm.setupMeta()
pm.create('Synthetic')
pm.load('Synthetic')
pm.meta.update(firstRun=False,defaultLang='en_US',updates=False,check_for_updates=False,check_for_addon_updates=False)
pm.profile['autoSync'] = False
pm.save()
pm.db.close()
import aqt
aqt.AnkiApp.KEY = 'anki-safe-sync-reviewer-test-' + str(os.getpid())
app = aqt._run(['anki','-b',str(base),'-p','Synthetic','--safemode'],exec=False)
assert app is not None, 'Independent test app did not start'
from aqt.qt import QEventLoop,QTimer,QFontDatabase,QFont
if pathlib.Path('C:/Windows/Fonts/arial.ttf').exists():
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/arial.ttf')
    app.setFont(QFont('Arial',10))


def pump(seconds=0.3):
    loop = QEventLoop()
    QTimer.singleShot(int(seconds*1000),loop.quit)
    loop.exec()


def js(code,web=None):
    answer = []
    (web or aqt.mw.web).evalWithCallback(code,answer.append)
    end = time.monotonic()+10
    while not answer and time.monotonic()<end: pump(0.05)
    assert answer, 'Reviewer JavaScript callback timed out'
    return answer[0]


try:
    for _ in range(100):
        pump(0.1)
        if aqt.mw.col and aqt.mw.state not in ('startup','profileManager'): break
    mw = aqt.mw
    assert mw.col, 'Synthetic collection not opened'
    spec = importlib.util.spec_from_file_location('fixture_tests',source/'test_types.py')
    fixtures = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fixtures)
    a = fixtures.a
    nodes = fixtures.fixtures()
    for node in nodes:
        h = fixtures.para('[Header] ReviewerMetadata <script>window.nsInjected=1</script> ')
        h['paragraph']['rich_text'].append({'type':'text','text':{'content':'PDF','link':{'url':'https://example.org/source.pdf'}}})
        node['_children'].append(h)
    values,media = fixtures.parsed(nodes)
    a.apply(mw.col,values,{'a'*32},{},media,{},a.approval_keys(values,{}))
    mw.col.decks.select(mw.col.decks.id('Synthetic'))
    mw.reset()
    pump(0.5)
    mw.moveToState('review')
    pump(1)
    r = mw.reviewer
    state = a.snapshot(mw.col)
    def question(bid,ordinal=None):
        ids = state[bid]['cards']
        r.card = mw.col.get_card(ids[ordinal or min(ids)])
        r.card.start_timer()
        r._showQuestion()
        pump(0.6)
    def mask_alpha(x,y):
        return js("(function(){var c=document.getElementById('image-occlusion-canvas');return c.getContext('2d').getImageData(Math.floor(c.width*"+str(x)+"),Math.floor(c.height*"+str(y)+"),1,1).data[3]})()")
    def show_answer():
        if r.state=='answer': return
        # Utility for layout checks: explicitly complete all sequence steps.
        js("if(window.nsSequence&&window.nsSequence.ready())while(window.nsSequence.remaining())window.nsSequence.step(false);true")
        r._showAnswer(); pump(.2)
    import aqt.webview as webmodule
    opened_links=[]
    webmodule.openLink=lambda url,*args,**kwargs:opened_links.append(str(url))
    import aqt.url_schemes as urlschemes
    urlschemes.open_url_if_supported_scheme=lambda url:opened_links.append(url.toString())
    def check_header():
        assert r.state=='answer'
        assert js("document.querySelectorAll('[data-ease]').length",r.bottom.web)>=2
        assert js("typeof window.nsInjected")=='undefined'
        assert js("!!document.querySelector('.ns-header')&&!document.querySelector('.ns-header').open")
        js("document.querySelector('.ns-header summary').click();true")
        assert js("document.querySelector('.ns-header').open")
        js("document.querySelector('.ns-header a').click();true")
        pump(.1)
        assert opened_links and opened_links[-1]=='https://example.org/source.pdf'
        assert r.state=='answer'
        js("document.querySelector('.ns-header summary').click();true")
        assert not js("document.querySelector('.ns-header').open")
    for bid,value in values.items():
        kind = value.get('kind','basic')
        question(bid)
        assert not js("!!document.querySelector('.ns-header')")
        if kind=='input':
            expected = 'Wien'
            assert js("!!document.getElementById('typeans')"), kind+' input missing'
            assert r.typeCorrect and expected in r.typeCorrect
            js("document.getElementById('typeans').value='"+expected+"';true")
            r._getTypedAnswer()
            pump(0.6)
            assert r.typedAnswer == expected
            assert js("!!document.querySelector('.typeGood')"), kind+' native comparison missing'
            check_header()
            print('PASS native reviewer typing:',kind)
        elif kind=='cloze_input':
            assert js("document.querySelectorAll('.ns-gap input.ns-inline-input').length")==1
            assert not js("!!document.getElementById('typeans')")
            js("var i=document.querySelector('.ns-inline-input');i.value='Jupiter';i.dispatchEvent(new Event('input',{bubbles:true}));true")
            r._getTypedAnswer(); pump(.5)
            assert js("document.querySelector('.ns-inline-feedback').dataset.correct")=='1'
            check_header()
            print('PASS actual reviewer: input located directly inside cloze, independent answer comparison')
        elif kind in ('image','images'):
            assert js("!!document.querySelector('#image-occlusion-canvas')"), 'Native IO canvas missing'
            assert js("document.querySelector('#image-occlusion-container img').naturalWidth") == 400
            assert js("document.getElementById('err').textContent") == ''
            assert mask_alpha(.25,.17)>0, 'Active rectangle not covering question'
            if kind=='images': assert mask_alpha(.7,.67)>0, 'Inactive rectangle not covering all-mode question'
            show_answer()
            pump(0.4)
            assert not js("!!document.querySelector('#toggle')")
            assert mask_alpha(.25,.17)==0, 'Active rectangle not revealed on answer'
            if kind=='images': assert mask_alpha(.7,.67)>0, 'Inactive rectangle unexpectedly revealed'
            check_header()
            print('PASS native reviewer image occlusion:',kind)
        elif kind=='sequence':
            # Select a real scheduler queue containing only the sequence card.
            sequence_id = r.card.id
            did = mw.col.decks.id('SyntheticSequence')
            mw.col.set_deck([sequence_id],did)
            mw.col.decks.select(did)
            mw.moveToState('overview')
            mw.reset()
            pump(0.3)
            mw.moveToState('review')
            pump(0.8)
            assert r.card.id==sequence_id
            assert js("document.querySelector('.ns-picture img').naturalWidth") == 400
            js("document.querySelector('.ns-picture').style.width='200px';true")
            pump(0.2)
            ratio = js("document.querySelector('.ns-mask').getBoundingClientRect().width/document.querySelector('.ns-picture img').getBoundingClientRect().width")
            assert abs(ratio-.3)<.01, 'Scaled mask not aligned to original image'
            assert js("Array.from(document.querySelectorAll('.ns-mask')).filter(m=>getComputedStyle(m).visibility!='hidden').length") == 2
            js("document.querySelector('.ns-next').click();true")
            assert js("Array.from(document.querySelectorAll('.ns-mask')).filter(m=>getComputedStyle(m).visibility!='hidden').length") == 1
            js("document.querySelector('.ns-next').click();true")
            assert js("Array.from(document.querySelectorAll('.ns-mask')).filter(m=>getComputedStyle(m).visibility!='hidden').length") == 0
            show_answer()
            pump(0.4)
            assert js("Array.from(document.querySelectorAll('.ns-mask')).filter(m=>getComputedStyle(m).visibility!='hidden').length") == 0
            assert r.state=='answer'
            check_header()
            reviewed_id = r.card.id
            r._answerCard(3)
            for _ in range(50):
                pump(0.1)
                if mw.col.get_card(reviewed_id).reps==1: break
            assert mw.col.get_card(reviewed_id).reps == 1
            print('PASS actual reviewer sequence button: 2 → 1 → 0 masks; normal answer state')
        else:
            assert js("document.getElementById('qa').textContent.length") > 0
            show_answer(); pump(.3); check_header()
    # The second supported native IO mode reveals inactive positions on the front.
    node = fixtures.fixtures()[5]
    node['_children'][-1] = fixtures.para('Modus: Eine verdecken, eine abfragen')
    one,one_media = fixtures.parsed([node])
    expanded = dict(values,**one)
    before = a.snapshot(mw.col)
    a.apply(mw.col,expanded,{'a'*32},before,one_media,{},a.approval_keys(expanded,before))
    mw.col.decks.select(mw.col.decks.id('Synthetic'))
    mw.moveToState('overview')
    mw.reset()
    pump(0.3)
    mw.moveToState('review')
    pump(0.6)
    state = a.snapshot(mw.col)
    question(node['id'])
    assert mask_alpha(.25,.17)>0 and mask_alpha(.7,.67)==0
    show_answer()
    pump(0.3)
    assert mask_alpha(.25,.17)==0
    print('PASS actual reviewer IO one-mode: only active mask is covered')
    # Multiple inline gaps, Unicode NFC equivalence, wrong answer and keyboard.
    node_inline=fixtures.toggle('[Lücke+Eingabe] Organisation',fixtures.para('A {{c1::Österreich}} · B {{c1::α & β}}.'))
    inline,inline_media=fixtures.parsed([node_inline]); expanded.update(inline)
    before=a.snapshot(mw.col)
    a.apply(mw.col,expanded,{'a'*32},before,inline_media,{},a.approval_keys(expanded,before))
    state=a.snapshot(mw.col); question(node_inline['id'])
    assert js("document.querySelectorAll('.ns-gap input.ns-inline-input').length")==2
    import json
    supplied=json.dumps(['O\u0308sterreich','α   &  β'])
    js("Array.from(document.querySelectorAll('.ns-inline-input')).forEach(function(i,n){i.value="+supplied+"[n];i.dispatchEvent(new Event('input',{bubbles:true}))});true")
    from PyQt6.QtTest import QTest
    from aqt.qt import Qt
    js("document.querySelector('.ns-inline-input').focus();true")
    QTest.keyClick(mw.web.focusProxy(),Qt.Key.Key_Tab); pump(.1)
    assert js("document.activeElement===document.querySelectorAll('.ns-inline-input')[1]")
    QTest.keyClick(mw.web.focusProxy(),Qt.Key.Key_Return); pump(.5)
    assert r.state=='answer'
    assert js("document.querySelectorAll('.ns-inline-feedback[data-correct=\"1\"]').length")==2
    question(node_inline['id'])
    assert js("Array.from(document.querySelectorAll('.ns-inline-input')).every(i=>i.value==='')")
    js("var i=document.querySelector('.ns-inline-input');i.value='falsch';i.dispatchEvent(new Event('input',{bubbles:true}));true")
    r._getTypedAnswer(); pump(.4)
    assert js("document.querySelectorAll('.ns-inline-feedback[data-correct=\"0\"]').length")==2
    assert mw.col.get_note(state[node_inline['id']]['nid']).cards()[0].reps==0
    print('PASS multiple inline fields: Unicode NFC/whitespace, Tab, Enter, correct/wrong feedback, no auto-grade, reset')
    # Every distinct note gets its own real native Qt editor, no grouping.
    mp = __import__('types_test.mask_preview',fromlist=['confirm'])
    editors=[]
    def accept_preview():
        from aqt.qt import QApplication
        d = QApplication.activeModalWidget()
        assert d.windowTitle() in ('Bildmasken bearbeiten','Bildreihenfolge bearbeiten')
        editors.append(d.value['block'])
        d.confirm()
        if len(editors)<3: QTimer.singleShot(100,accept_preview)
    QTimer.singleShot(100,accept_preview)
    assert mp.confirm(mw,values,{},media)
    assert len(editors)==3 and len(set(editors))==3
    print('PASS per-note mask editors: three separate controls for identical original image')
    # 1.4: install the actual Reviewer bridge, then drive its real JS message,
    # QueryOp, native dialog and CollectionOp with no Notion request available.
    from unittest.mock import patch
    local_ui=__import__('types_test.local_mask_ui',fromlist=['start'])
    sync_ui=__import__('types_test.ui',fromlist=['install'])
    bridge=__import__('types_test.reviewer_masks',fromlist=['install'])
    local=__import__('types_test.local_masks',fromlist=['save'])
    sync_ui.mw=mw; bridge.install()
    failures=[]
    def failure(error):
        failures.append(str(error)); sync_ui.busy=False
    sync_ui.finish_error=failure
    assert bridge.bridge((False,None),'nss-mask-edit:bogus',object())==(True,None)
    def wait_idle(predicate=lambda:True):
        end=time.monotonic()+12
        while time.monotonic()<end:
            pump(.05)
            if not sync_ui.busy and predicate(): break
        assert not sync_ui.busy and predicate(), 'Local operation timed out'
        assert not failures, failures
    def click_editor(action,expected_nid,expected_mask=None):
        calls=[]
        def drive():
            from aqt.qt import QApplication
            d=QApplication.activeModalWidget()
            if d is None: QTimer.singleShot(40,drive); return
            try:
                assert isinstance(d,local_ui.MaskEditor), type(d)
                assert d.value['nid']==expected_nid
                if expected_mask is not None: assert d.items[expected_mask].isSelected()
                calls.append(d.value['block'])
                if action=='cancel':
                    d.items[min(d.items)].apply_drag('move',d.items[min(d.items)].rect(),QPointF(10,5)); d.reject()
                elif action=='save':
                    mid=expected_mask or min(d.items)
                    d.items[mid].apply_drag('move',d.items[mid].rect(),QPointF(12,4)); d.confirm()
                elif action=='remove': d.remove(1); d.confirm()
                else: d.confirm()
            except Exception as error:
                failures.append(str(error)); d.reject()
        from aqt.qt import QPointF
        QTimer.singleShot(120,drive)
        js("document.getElementById('ns-mask-edit').click();true")
        wait_idle(lambda:bool(calls))
        pump(.4)
        assert len(calls)==1
    with patch.object(fixtures.c,'request',side_effect=AssertionError('Notion network forbidden')),patch.object(sync_ui.Fetcher,'tree',side_effect=AssertionError('Notion fetch forbidden')):
        state=a.snapshot(mw.col)
        for bid in [b for b,v in values.items() if v.get('kind') in ('image','images','sequence')]:
            value=values[bid]; ordinal=2 if value['kind']=='images' else 1
            question(bid,ordinal)
            cid=r.card.id; nid=r.card.nid; reps=mw.col.get_card(cid).reps
            assert js("document.querySelectorAll('#ns-mask-edit').length")==1
            assert not js("!!document.querySelector('#toggle')")
            assert 'ns-mask-edit' not in r.card.question(), 'Button must not leak into unsupported clients'
            assert 'ns-mask-edit' not in bridge.render('preview',r.card,'previewQuestion')
            original=a.snapshot(mw.col)
            click_editor('cancel',nid,ordinal if value['kind']!='sequence' else None)
            assert a.snapshot(mw.col)==original
            click_editor('save',nid,ordinal if value['kind']!='sequence' else None)
            assert r.card.id==cid and r.state=='question'
            assert mw.col.get_card(cid).reps==reps
            assert a.snapshot(mw.col)[bid]['cards']==original[bid]['cards']
            assert a.snapshot(mw.col)[bid]['masks']!=original[bid]['masks']
            show_answer(); pump(.4)
            assert js("document.querySelectorAll('#ns-mask-edit').length")==1
            click_editor('save',nid,ordinal if value['kind']!='sequence' else None)
            assert r.card.id==cid and r.state=='answer' and mw.col.get_card(cid).reps==reps
            after=a.snapshot(mw.col)
            click_editor('noop',nid,ordinal if value['kind']!='sequence' else None)
            assert a.snapshot(mw.col)==after
            if value['kind']=='sequence':
                question(bid); assert js("!!document.querySelector('.ns-next')")
            print('PASS local Reviewer bridge: correct note/mask, cancel/save/noop, same card/side, no rating:',value['kind'])
        # Deletion from the displayed multi-card note, while card 2 remains.
        bid=next(b for b,v in values.items() if v.get('kind')=='images')
        state=a.snapshot(mw.col); question(bid,2); nid=r.card.nid; cid=r.card.id
        original=a.snapshot(mw.col)
        with patch.object(local_ui,'askUser',return_value=False) as approval:
            click_editor('remove',nid,2)
            assert approval.called and str(original[bid]['cards'][1]) in approval.call_args[0][0]
        assert a.snapshot(mw.col)==original
        with patch.object(local_ui,'askUser',return_value=True): click_editor('remove',nid,2)
        assert r.card.id==cid and r.state=='question'
        assert a.snapshot(mw.col)[bid]['cards']=={2:cid}
        print('PASS actual Reviewer deletion: exact card preview, refusal unchanged, approval preserves sibling')
        # Explicitly removing the displayed card cannot render that deleted ID.
        # End at overview with an explanation, without nextCard or a rating.
        state=a.snapshot(mw.col)
        removed_bid=next(b for b,v in state.items() if v['kind']=='images' and len(v['ids'])==2)
        question(removed_bid,1); nid=r.card.nid; deleted_cid=r.card.id; messages=[]
        with patch.object(local_ui,'askUser',return_value=True),patch.object(local_ui,'showInfo',side_effect=lambda message,**kw:messages.append(message)),patch.object(r,'nextCard',side_effect=AssertionError('Must not advance')):
            click_editor('remove',nid,1)
        assert mw.state=='overview' and messages and str(deleted_cid) not in str(a.snapshot(mw.col)[removed_bid]['cards'].values())
        mw.moveToState('review'); pump(.5)
        print('PASS displayed-card deletion: explicit approval ends at overview, no nextCard or rating')
        # Real menu selection, multiple notes, abort second => all drafts lost.
        original=a.snapshot(mw.col); dialogs=[]
        def select_and_abort():
            from aqt.qt import QApplication,QTableWidget
            d=QApplication.activeModalWidget()
            if d is None: QTimer.singleShot(40,select_and_abort); return
            try:
                table=d.findChild(QTableWidget)
                if table:
                    table.selectAll(); d.accept(); QTimer.singleShot(60,select_and_abort)
                else:
                    dialogs.append(d.value['nid'])
                    if len(dialogs)==1:
                        d.items[min(d.items)].apply_drag('move',d.items[min(d.items)].rect(),QPointF(8,4)); d.confirm()
                        QTimer.singleShot(60,select_and_abort)
                    else: d.reject()
            except Exception as error: failures.append(str(error)); d.reject()
        from aqt.qt import QPointF
        QTimer.singleShot(100,select_and_abort); local_ui.start(); wait_idle(lambda:len(dialogs)==2)
        assert a.snapshot(mw.col)==original and len(set(dialogs))==2
        print('PASS actual local menu: multi-select notes, separate editors, abort second discards first draft')
    # Responsive Header spacing in the actual reviewer, all seven types and
    # both body themes. details stays absent on the question and starts closed.
    state=a.snapshot(mw.col)
    for bid in values:
        question(bid)
        assert not js("!!document.querySelector('.ns-header')")
        show_answer(); pump(.2)
        for width in (540,1200):
            mw.resize(width,800); pump(.1)
            for dark in (False,True):
                js("document.body.classList.toggle('nightMode',"+str(dark).lower()+");document.body.classList.toggle('night_mode',"+str(dark).lower()+");true")
                geometry=js("(function(){var h=document.querySelector('.ns-header'),c=getComputedStyle(h);return [h.open,parseFloat(c.marginTop)/parseFloat(c.fontSize),parseFloat(c.borderTopWidth)]})()")
                assert geometry[0] is False and 1.9<=geometry[1]<=4.6 and geometry[2]>=1,geometry
        print('PASS Header spacing/light/dark:',values[bid].get('kind','basic'))
    # 1.5 visual QA in the actual Reviewer, including its IO canvas and inputs.
    screenshots=scratch/'design-reviewer'; screenshots.mkdir(exist_ok=True)
    for bid,value in values.items():
        kind=value.get('kind','basic')
        for dark in (False,True):
            question(bid); show_answer(); pump(.2)
            js("document.body.classList.toggle('nightMode',"+str(dark).lower()+");document.body.classList.toggle('night_mode',"+str(dark).lower()+");true")
            colors=js("(function(){var c=getComputedStyle(document.body);return [c.color,c.backgroundColor]})()")
            assert colors[0]!=colors[1]
            assert colors[1]==('rgb(28, 28, 30)' if dark else 'rgb(245, 245, 247)'),colors
            ratio=js("(function(){var c=getComputedStyle(document.body);function l(s){var a=s.match(/\\d+/g).slice(0,3).map(x=>Number(x)/255).map(x=>x<=.04045?x/12.92:Math.pow((x+.055)/1.055,2.4));return a[0]*.2126+a[1]*.7152+a[2]*.0722}var a=[l(c.color),l(c.backgroundColor)].sort((x,y)=>x-y);return (a[1]+.05)/(a[0]+.05)})()")
            assert ratio>=4.5,ratio
            for width in (320,768,1100):
                mw.web.setFixedWidth(width); pump(.2)
                for font in ('20px','30px'):
                    js("document.body.style.fontSize='"+font+"';true")
                    assert js("document.documentElement.scrollWidth<=document.documentElement.clientWidth+1"), (kind,width,font)
            mw.web.setFixedWidth(768); js("document.body.style.fontSize='20px';true"); pump(.2)
            mw.web.grab().save(str(screenshots/(kind+('-dark' if dark else '-light')+'.png')))
            if kind in ('image','images','sequence'):
                target=js("(function(){var b=document.getElementById('ns-mask-edit').getBoundingClientRect();return [b.width,b.height]})()")
                assert min(target)>=44,target
            if kind=='sequence':
                question(bid); pump(.2)
                assert js("document.querySelector('.ns-next').textContent")=='Weiter aufdecken'
                assert js("Array.from(document.querySelectorAll('.ns-mask')).every(m=>m.tabIndex===-1)")
        print('PASS unified design, 320/768/1100px, 150% text, light/dark:',kind)
    mw.web.setMinimumWidth(0); mw.web.setMaximumWidth(16777215)
    # A migrated legacy card gets the same desktop presentation without
    # changing a shared old notetype or styling its unrelated foreign notes.
    legacy_model=mw.col.models.new('Notion-Basic')
    for name in ('Front','Back','NotionID','LastSync'): mw.col.models.add_field(legacy_model,mw.col.models.new_field(name))
    legacy_template=mw.col.models.new_template('Legacy')
    legacy_template['qfmt']='{{Front}}'; legacy_template['afmt']='{{FrontSide}}<hr id="answer">{{Back}}'
    mw.col.models.add_template(legacy_model,legacy_template); mw.col.models.add(legacy_model)
    legacy=fixtures.toggle('Ältere Frage',fixtures.para('Antwort'),fixtures.para('[Header] Quelle'))
    n=mw.col.new_note(legacy_model); n['Front']='Ältere Frage'; n['Back']='Antwort'; n['NotionID']='https://notion.so/'+'a'*32+'#'+legacy['id']
    mw.col.add_note(n,mw.col.decks.id('Synthetic'))
    imported,_=fixtures.parsed([legacy]); before=a.snapshot(mw.col)
    union=dict(expanded,**imported)
    a.apply(mw.col,union,{'a'*32},before,{}, {},a.approval_keys(union,before))
    state=a.snapshot(mw.col); question(legacy['id'])
    assert js("!!document.querySelector('.ns-card')")
    assert js("getComputedStyle(document.body).fontFamily.includes('Segoe UI')")
    assert 'ns-design-v1' not in mw.col.models.get(legacy_model['id'])['css']
    foreign=mw.col.new_note(mw.col.models.get(legacy_model['id'])); foreign['Front']='Unverwaltet'; foreign['Back']='Antwort'; mw.col.add_note(foreign,mw.col.decks.id('Synthetic'))
    r.card=foreign.cards()[0]
    assert bridge.render('Untouched',r.card,'reviewQuestion')=='Untouched'
    print('PASS legacy desktop presentation: shared model and foreign notes unchanged')
    mw.col.remove_notes([foreign.id])
    # 1.6: strongly portrait/landscape images in low/narrow viewports and real
    # fullscreen, with the actual image/canvas/masks kept in the same DOM node.
    import struct,zlib
    def image_png(width,height):
        def chunk(tag,data): return struct.pack('!I',len(data))+tag+data+struct.pack('!I',zlib.crc32(tag+data)&0xffffffff)
        rows=b''.join(b'\0'+bytes([210,225,240])*width for _ in range(height))
        return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!2I5B',width,height,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b'')
    probes={}; probe_media={}
    for width,height in ((1200,300),(300,1200)):
        probe_nodes=fixtures.fixtures()[4:]
        probe_nodes.append(fixtures.toggle('Bildfrage',fixtures.image(),fixtures.para('Antwort')))
        renderer=fixtures.c.Renderer(lambda *_,data=image_png(width,height):(data,'image/png'))
        parsed=fixtures.c.parse(probe_nodes,'b'*32,'AspectRatio',renderer)
        probes.update(parsed); probe_media.update(renderer.media)
        before=a.snapshot(mw.col)
        a.apply(mw.col,probes,{'b'*32},before,probe_media,{},a.approval_keys(probes,before))
        state=a.snapshot(mw.col)
        for bid,value in parsed.items():
            kind=value.get('kind','basic'); question(bid)
            for viewport_width,viewport_height in ((320,250),(520,340),(1100,500)):
                mw.web.setFixedSize(viewport_width,viewport_height); pump(.25)
                geometry=js("(function(){var i=document.querySelector('.ns-card img'),r=i.getBoundingClientRect();return [r.width,r.height,i.naturalWidth/i.naturalHeight]})()")
                assert abs(geometry[0]/geometry[1]-geometry[2])<.005,(kind,geometry)
                if kind in ('image','images'):
                    aligned=js("(function(){var a=document.querySelector('#image-occlusion-container img').getBoundingClientRect(),b=document.getElementById('image-occlusion-canvas').getBoundingClientRect();return [a.width-b.width,a.height-b.height]})()")
                    assert all(abs(n)<2 for n in aligned),(kind,aligned)
            fitted=[]
            for vw,vh in ((320,600),(1000,900)):
                mw.web.setFixedSize(vw,vh); pump(.4)
                geometry=js("(function(){var i=document.querySelector('.ns-card img').getBoundingClientRect(),f=document.querySelector('.ns-local-actions'),c=document.querySelector('.ns-card').getBoundingClientRect();return [i.width,i.height,i.bottom,f?f.getBoundingClientRect().top:c.bottom,f?f.getBoundingClientRect().bottom:c.bottom,innerHeight]})()")
                assert geometry[2]<=geometry[3]+1,(kind,geometry)
                assert geometry[4]<=geometry[5]+1,(kind,geometry)
                fitted.append(geometry)
            assert fitted[1][0]>fitted[0][0],(kind,fitted)
            mw.web.grab().save(str(screenshots/('fitted-'+kind+'-'+str(width)+'x'+str(height)+'.png')))
            mw.web.setMinimumSize(0,0); mw.web.setMaximumSize(16777215,16777215); mw.resize(900,800); pump(.2)
            question(bid)
            if kind=='sequence':
                js("document.querySelector('.ns-next').click();true")
                assert js('window.nsSequence.remaining()')==1
            alpha_before=(mask_alpha(.25,.17)>0,mask_alpha(.7,.67)>0) if kind in ('image','images') else None
            window_state=mw.windowState(); side=r.state; reps=mw.col.get_card(r.card.id).reps
            js("document.querySelector('.ns-zoomable').dataset.original='yes';document.querySelector('.ns-zoomable').click();true")
            pump(.5)
            assert mw.windowState()==window_state and not mw.isFullScreen(),kind
            assert js("!!document.querySelector('.ns-zoom[role=dialog]')")
            assert js("document.querySelector('.ns-zoom-target').dataset.original")=='yes'
            fit=js("(function(){var p=document.querySelector('.ns-zoom-body').getBoundingClientRect(),i=document.querySelector('.ns-zoom img'),r=i.getBoundingClientRect();return [r.width/r.height-i.naturalWidth/i.naturalHeight,r.width<=p.width+1,r.height<=p.height+1]})()")
            assert abs(fit[0])<.005 and fit[1] and fit[2],(kind,fit)
            if kind=='sequence': assert js('window.nsSequence.remaining()')==1
            if alpha_before is not None: assert (mask_alpha(.25,.17)>0,mask_alpha(.7,.67)>0)==alpha_before
            mw.web.grab().save(str(screenshots/('fullscreen-'+kind+'-'+str(width)+'x'+str(height)+'.png')))
            QTest.keyClick(mw.web.focusProxy(),Qt.Key.Key_Escape); pump(.5)
            assert not js("!!document.querySelector('.ns-zoom')")
            assert mw.windowState()==window_state and r.state==side
            assert mw.col.get_card(r.card.id).reps==reps
            assert js("!!document.querySelector('.ns-card [data-original=yes]')")
            if kind=='sequence': assert js('window.nsSequence.remaining()')==1
            if alpha_before is not None: assert (mask_alpha(.25,.17)>0,mask_alpha(.7,.67)>0)==alpha_before
            print('PASS aspect ratio + fullscreen/Escape preserves content and masks:',kind,width,height)
    # True desktop key events must step, never expose the whole sequence.
    seq=next(b for b,v in probes.items() if v.get('kind')=='sequence')
    state=a.snapshot(mw.col); question(seq); cid=r.card.id; reps=mw.col.get_card(cid).reps
    for key,remaining in ((Qt.Key.Key_Space,1),(Qt.Key.Key_Return,0)):
        mw.web.setFocus(); QTest.keyClick(mw.web.focusProxy(),key); pump(.4)
        assert r.state==('question' if remaining else 'answer')
        if remaining: assert js('window.nsSequence.remaining()')==remaining
        assert mw.col.get_card(cid).reps==reps
        from aqt.qt import QKeyEvent,QEvent,QApplication
        for _ in range(4): QApplication.sendEvent(mw.web.focusProxy(),QKeyEvent(QEvent.Type.KeyPress,key,Qt.KeyboardModifier.NoModifier,' ',True,1))
        pump(.1); assert r.state==('question' if remaining else 'answer')
    assert r.state=='answer' and mw.col.get_card(cid).reps==reps
    question(seq)
    js("document.getElementById('ansbut').click();true",r.bottom.web); pump(.4)
    assert r.state=='question' and js('window.nsSequence.remaining()')==1
    js("document.querySelector('.ns-reset').click();true"); assert js('window.nsSequence.remaining()')==2
    r._showAnswer(); pump(.4); assert r.state=='question' and js('window.nsSequence.remaining()')==1
    r._showAnswer(); pump(.4); assert r.state=='answer' and mw.col.get_card(cid).reps==reps
    question(seq)
    for _ in range(2): js("document.querySelector('.ns-next').click();true"); pump(.4)
    assert r.state=='answer' and mw.col.get_card(cid).reps==reps
    print('PASS force sequence: Space/Return/Enter, native answer button, reset, direct answer path; no rating before completion')
    print('ACTUAL REVIEWER TEST PASSED (synthetic profile only)')
except Exception:
    traceback.print_exc()
    os._exit(1)
finally:
    # The profile is synthetic, no production profile was opened.
    if aqt.mw.col:
        aqt.mw.col.close()
os._exit(0)
