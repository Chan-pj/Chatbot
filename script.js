(function(){
  var FLASK = window.location.origin;
  var ICON = 'logo.png';

  // 로고 아이콘
  if (document.getElementById('logo-img')) document.getElementById('logo-img').src = ICON;
  if (document.getElementById('topbar-img')) document.getElementById('topbar-img').src = ICON;

  var cu = null, dark = false, sess = [], cid = null, favs = [];

  // 로컬 스토리지 키
  function sk(){ return 'bb_' + cu.username + '_s'; }
  function ck(){ return 'bb_' + cu.username + '_c'; }
  function fk(){ return 'bb_' + cu.username + '_f'; }

  function save(){ if(!cu) return; localStorage.setItem(sk(), JSON.stringify(sess)); localStorage.setItem(ck(), cid || ''); }
  function load(){ try{ var d = localStorage.getItem(sk()); sess = d ? JSON.parse(d) : []; cid = localStorage.getItem(ck()) || null; }catch(e){ sess = []; cid = null; } }
  function loadF(){ try{ var d = localStorage.getItem(cu ? fk() : 'bokbok_guest_f'); favs = d ? JSON.parse(d) : []; }catch(e){ favs = []; } }
  function saveF(){ localStorage.setItem(cu ? fk() : 'bokbok_guest_f', JSON.stringify(favs)); }
  function gid(){ return 'sess_' + Date.now(); }

  // 다크모드 제어
  function tDark(){ dark = !dark; document.body.classList.toggle('dark', dark); document.getElementById('dark-btn').textContent = dark ? '☀️' : '🌙'; localStorage.setItem('bb_dark', dark); }
  if(localStorage.getItem('bb_dark') === 'true') tDark();

  function showL(){ document.getElementById('register-modal').style.display = 'none'; document.getElementById('login-modal').style.display = 'flex'; document.getElementById('login-error').textContent = ''; }
  function showR(){ document.getElementById('login-modal').style.display = 'none'; document.getElementById('register-modal').style.display = 'flex'; document.getElementById('reg-error').textContent = ''; }

  // 로그인
  async function doLogin(){
    var u = document.getElementById('login-username').value.trim(), p = document.getElementById('login-password').value.trim();
    if(!u || !p){ document.getElementById('login-error').textContent = '아이디와 비밀번호를 입력하세요.'; return; }
    var r = await fetch(FLASK + '/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ username: u, password: p }) });
    var d = await r.json();
    if(d.success){ cu = { username: d.username, role: d.role, region: d.region || '' }; document.getElementById('login-modal').style.display = 'none'; load(); loadF(); rUI(); if(cid && sess.find(function(s){ return s.id === cid; })) sw(cid); else if(sess.length > 0) sw(sess[0].id); else nChat(); }
    else document.getElementById('login-error').textContent = d.message;
  }

  // 회원가입
  async function doReg(){
    var u = document.getElementById('reg-username').value.trim(), p = document.getElementById('reg-password').value.trim(), p2 = document.getElementById('reg-password2').value.trim(), e = document.getElementById('reg-error');
    if(!u || !p){ e.textContent = '모든 항목을 입력하세요.'; return; }
    if(p !== p2){ e.textContent = '비밀번호가 일치하지 않습니다.'; return; }
    var r = await fetch(FLASK + '/register', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ username: u, password: p, region: (document.getElementById('reg-sido').value + ' ' + document.getElementById('reg-sigungu').value).trim() }) });
    var d = await r.json();
    if(d.success){ e.style.color = '#4a9e4a'; e.textContent = '가입 완료! 로그인해주세요.'; setTimeout(showL, 1000); }
    else{ e.style.color = '#e05555'; e.textContent = d.message; }
  }

  // 로그아웃
  async function doOut(){
    await fetch(FLASK + '/logout', { method: 'POST', credentials: 'include' });
    cu = null; sess = []; cid = null; favs = []; rUI();
    document.getElementById('session-list').innerHTML = ''; document.getElementById('chat-area').innerHTML = '';
    document.getElementById('login-username').value = ''; document.getElementById('login-password').value = '';
    document.getElementById('logout-modal').style.display = 'flex';
  }

  function rUI(){
    var a = document.getElementById('user-info-area'), aa = document.getElementById('admin-btn-area'), lb = document.getElementById('logout-btn');
    if(cu){ a.innerHTML = '<i class="ti ti-user-circle" style="color:#5cb85c;font-size:16px;"></i> ' + cu.username; lb.style.display = 'flex'; aa.innerHTML = ''; if(cu.role === 2){ var b = document.createElement('button'); b.className = 'sidebar-btn admin'; b.innerHTML = '<i class="ti ti-shield-check"></i> 관리자 페이지'; b.onclick = adm; aa.appendChild(b); } }
    else{ a.innerHTML = ''; aa.innerHTML = ''; lb.style.display = 'none'; }
  }

  function oRec(){ document.getElementById('recommend-modal').style.display = 'flex'; }
  
  // 맞춤 정책 추천
  async function doRec(){
    var age = document.getElementById('rec-age').value, hh = document.getElementById('rec-household').value, inc = document.getElementById('rec-income').value, cat = document.getElementById('rec-category').value;
    if(!age || !hh || !inc || !cat){ alert('모든 항목을 입력해주세요.'); return; }
    var q = age + '세 ' + hh + ' 월소득 ' + inc + '만원 ' + cat + ' 복지 정책 추천';
    document.getElementById('recommend-modal').style.display = 'none';
    if(!cid) nChat();
    bub('user', '나이: ' + age + '세 / 가구: ' + hh + ' / 소득: ' + inc + '만원 / 관심: ' + cat + ' 맞춤 복지 정책 추천해줘!');
    typ();
    try{ var r = await fetch(FLASK + '/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ message: q, session_id: cid }) }); var d = await r.json(); untyp(); bub('bot', d.reply || '추천 정책을 가져오지 못했어요.'); }
    catch(e){ untyp(); bub('bot', '서버에 연결할 수 없습니다.'); }
  }

  // 즐겨찾기
  function oFav(){
    var l = document.getElementById('fav-list'); l.innerHTML = '';
    if(favs.length === 0){ var p = document.createElement('p'); p.style.cssText = 'color:var(--tx3);font-size:13px;text-align:center;padding:20px;'; p.textContent = '즐겨찾기한 답변이 없어요.'; l.appendChild(p); } 
    else {
      favs.forEach(function(f, i){ 
        var it = document.createElement('div'); it.className = 'fav-item'; it.style.cssText = 'margin-bottom: 12px; border: .5px solid var(--bd); border-radius: 10px; background: var(--cb); overflow: hidden; display: flex; flex-direction: column;';
        var hdr = document.createElement('div'); hdr.className = 'fav-item-header'; hdr.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 12px 14px; gap: 8px;';
        var title = document.createElement('div'); title.className = 'fav-item-title'; title.style.cssText = 'font-size: 14px; font-weight: 600; color: var(--tx); flex: 1;'; title.textContent = f.title || '알 수 없는 정책';
        var actions = document.createElement('div'); actions.className = 'fav-item-actions'; actions.style.cssText = 'display: flex; align-items: center; gap: 8px;';
        var delB = document.createElement('button'); delB.className = 'fav-remove'; delB.innerHTML = '<i class="ti ti-trash"></i>'; delB.style.cssText = 'background: none; border: none; cursor: pointer; color: #e05555; font-size: 14px;'; delB.onclick = (function(x){ return function(e){ e.stopPropagation(); rmFav(x); }; })(i);
        actions.appendChild(delB); hdr.appendChild(title); hdr.appendChild(actions); it.appendChild(hdr);
        var body = document.createElement('div'); body.className = 'fav-item-body open'; body.style.cssText = 'padding: 0 14px 12px; border-top: .5px solid var(--bd); background: var(--sb); display: block;';
        if (f.org) { var orgRow = document.createElement('div'); orgRow.className = 'fav-body-row'; orgRow.style.cssText = 'display: flex; gap: 6px; font-size: 13px; margin-top: 8px;'; orgRow.innerHTML = '<span class="fav-body-label" style="color:var(--tx3); min-width:52px; flex-shrink:0;">주관기관</span><span class="fav-body-val" style="color:var(--tx2); line-height:1.5;">' + f.org + (f.region ? ' (' + f.region + ')' : '') + '</span>'; body.appendChild(orgRow); }
        if (f.desc) { var descRow = document.createElement('div'); descRow.className = 'fav-body-row'; descRow.style.cssText = 'display: flex; gap: 6px; font-size: 13px; margin-top: 8px;'; descRow.innerHTML = '<span class="fav-body-label" style="color:var(--tx3); min-width:52px; flex-shrink:0;">내용요약</span><span class="fav-body-val" style="color:var(--tx2); line-height:1.5;">' + f.desc + '</span>'; body.appendChild(descRow); }
        if (f.link) { var linkA = document.createElement('a'); linkA.className = 'fav-body-link'; linkA.href = f.link; linkA.target = '_blank'; linkA.style.cssText = 'display: inline-flex; align-items: center; gap: 4px; font-size: 12px; padding: 5px 12px; border-radius: 6px; border: .5px solid #4a9e4a; background: #f0f9e8; color: #2d6a2d; text-decoration: none; margin-top: 10px;'; linkA.innerHTML = '<i class="ti ti-external-link"></i> 복지로에서 확인하기'; body.appendChild(linkA); }
        if (f.keyword) { var kwRow = document.createElement('div'); kwRow.className = 'wc-keyword'; kwRow.style.cssText = 'display:flex; align-items:center; justify-content:space-between; gap:8px; font-size:12px; color:var(--tx3); background:var(--sh); padding:6px 10px; border-radius:6px; margin-top:8px;'; var kwText = document.createElement('span'); kwText.textContent = '검색창에 "' + f.keyword + '"로 검색해주세요'; var copyBtn = document.createElement('button'); copyBtn.className = 'wc-copy-btn'; copyBtn.style.cssText = 'background:none; border:none; cursor:pointer; color:#4a9e4a; font-size:14px; flex-shrink:0;'; copyBtn.innerHTML = '<i class="ti ti-copy"></i>'; copyBtn.onclick = (function(kw, btn){ return function(e){ e.stopPropagation(); navigator.clipboard.writeText(kw).then(function(){ btn.innerHTML = '<i class="ti ti-check"></i>'; setTimeout(function(){ btn.innerHTML = '<i class="ti ti-copy"></i>'; }, 1500); }); }; })(f.keyword, copyBtn); kwRow.appendChild(kwText); kwRow.appendChild(copyBtn); body.appendChild(kwRow); }
        it.appendChild(body); l.appendChild(it); 
      });
    }
    document.getElementById('fav-modal').style.display = 'flex';
  }

  function addFav(t){ saveF(); }
  function rmFav(i){ var removed = favs[i]; favs.splice(i, 1); saveF(); if(removed && removed.title){ document.querySelectorAll('.fav-btn.active').forEach(function(btn){ if(btn.dataset.title === removed.title){ btn.textContent = '☆'; btn.classList.remove('active'); } }); } oFav(); }

  // 회원 관리 (관리자)
  async function adm(){
    var r = await fetch(FLASK + '/admin/users', { credentials: 'include' }); var d = await r.json();
    if(d.error){ alert(d.error); return; }
    var tb = document.getElementById('admin-user-list'); tb.innerHTML = '';
    d.users.forEach(function(u){ var tr = document.createElement('tr'); tr.id = 'ur' + u.id; var t1 = document.createElement('td'); t1.textContent = u.username; var t2 = document.createElement('td'); var bg = document.createElement('span'); bg.className = 'role-badge ' + (u.role === 2 ? 'admin' : 'user'); bg.textContent = u.role === 2 ? '관리자' : '일반'; t2.appendChild(bg); var t3 = document.createElement('td'); t3.textContent = u.created_at ? u.created_at.slice(0, 10) : '-'; var t4 = document.createElement('td'); if(u.role !== 2){ var b = document.createElement('button'); b.className = 'del-user-btn'; b.textContent = '탈퇴'; b.onclick = (function(id){ return function(){ delU(id); }; })(u.id); t4.appendChild(b); }else t4.textContent = '-'; tr.appendChild(t1); tr.appendChild(t2); tr.appendChild(t3); tr.appendChild(t4); tb.appendChild(tr); });
    document.getElementById('admin-modal').style.display = 'flex';
  }

  async function delU(id){ if(!confirm('정말 탈퇴시키겠습니까?')) return; var r = await fetch(FLASK + '/admin/users/' + id, { method: 'DELETE', credentials: 'include' }); var d = await r.json(); if(d.success){ var row = document.getElementById('ur' + id); if(row) row.remove(); } }

  function mkE(){
    var w = document.createElement('div'); w.className = 'empty-state'; w.id = 'empty-state';
    var av = document.createElement('div'); av.className = 'empty-avatar'; var img = document.createElement('img'); img.src = ICON; img.style.cssText = 'width:50px;height:50px;object-fit:contain;'; av.appendChild(img); w.appendChild(av);
    var h = document.createElement('h2'); h.textContent = '안녕하세요! 저는 복복이예요'; w.appendChild(h);
    var p = document.createElement('p'); p.textContent = '궁금한 복지 정책을 검색해보세요'; w.appendChild(p);
    var row = document.createElement('div'); row.className = 'chip-row';
    var cs = [['🎯 나에게 맞는 복지정책 찾기', 'chip featured', oRec], ['🔥 인기 복지', 'chip', function(){ qk('인기 복지 서비스 알려줘'); }], ['💎 숨겨진 혜택', 'chip', function(){ qk('숨겨진 복지 혜택 알려줘'); }], ['청년 지원', 'chip', function(){ qk('청년 지원 정책'); }], ['노인 복지', 'chip', function(){ qk('노인 복지 서비스'); }], ['장애인 지원', 'chip', function(){ qk('장애인 지원'); }], ['육아·보육', 'chip', function(){ qk('육아 보육 혜택'); }]];
    cs.forEach(function(c){ var el = document.createElement('div'); el.className = c[1]; el.textContent = c[0]; el.onclick = c[2]; row.appendChild(el); });
    w.appendChild(row); return w;
  }

  function nChat(){ var id = gid(); sess.unshift({ id: id, title: '새 대화', msgs: [] }); save(); sw(id); }
  function dSess(e, id){ e.stopPropagation(); sess = sess.filter(function(s){ return s.id !== id; }); if(cid === id) cid = sess.length > 0 ? sess[0].id : null; save(); if(cid) sw(cid); else nChat(); }

  function sw(id){
    cid = id; save(); rSess();
    var s = sess.find(function(x){ return x.id === id; });
    var area = document.getElementById('chat-area'); area.innerHTML = '';
    if(!s || s.msgs.length === 0) area.appendChild(mkE());
    else s.msgs.forEach(function(m){ bub(m.role, m.text, false); });
    document.getElementById('topbar-title').textContent = (s && s.title !== '새 대화') ? s.title : '복지 정책 안내 챗봇';
  }

  function rSess(){
    var l = document.getElementById('session-list'); l.innerHTML = '';
    sess.forEach(function(s){ var d = document.createElement('div'); d.className = 'session-item' + (s.id === cid ? ' active' : ''); d.onclick = (function(sid){ return function(){ sw(sid); }; })(s.id); var sp = document.createElement('span'); sp.className = 'session-title'; sp.textContent = s.title; var b = document.createElement('button'); b.className = 'del-btn'; b.innerHTML = '<i class="ti ti-trash"></i>'; b.onclick = (function(sid){ return function(e){ dSess(e, sid); }; })(s.id); d.appendChild(sp); d.appendChild(b); l.appendChild(d); });
  }

  function isFaved(title){ return favs.some(function(f){ return typeof f === 'object' && f.title === title; }); }

  function renderCards(data){
    var wrap = document.createElement('div');
    if(data.intro){ var intro = document.createElement('div'); intro.className = 'welfare-intro'; intro.textContent = data.intro; wrap.appendChild(intro); }
    var cards = document.createElement('div'); cards.className = 'welfare-cards';
    (data.cards||[]).forEach(function(c){
      var card = document.createElement('div'); card.className = 'welfare-card';
      var hdr = document.createElement('div'); hdr.className = 'wc-header';
      var title = document.createElement('div'); title.className = 'wc-title'; title.textContent = c.title || '';
      hdr.appendChild(title);
      if(c.online==='Y'){ var badge = document.createElement('span'); badge.className = 'wc-badge'; badge.textContent = '온라인 신청'; hdr.appendChild(badge); }
      var fb = document.createElement('button');
      var faved = isFaved(c.title);
      fb.className = 'fav-btn' + (faved ? ' active' : '');
      fb.textContent = faved ? '⭐' : '☆';
      fb.title = '즐겨찾기';
      fb.style.fontSize = '20px'; fb.dataset.title = c.title || '';
      fb.onclick = (function(card){ return function(e){
        e.stopPropagation();
        var idx = favs.findIndex(function(f){ return typeof f === 'object' && f.title === card.title; });
        if(idx > -1){ favs.splice(idx, 1); fb.textContent = '☆'; fb.classList.remove('active'); }
        else { favs.unshift({ title: card.title, org: card.org || '', region: card.region || '', desc: card.desc || '', target: card.target || '', support: card.support || '', how: card.how || '', online: card.online || '', link: card.link || '', keyword: card.keyword || card.title || '' }); fb.textContent = '⭐'; fb.classList.add('active'); }
        saveF();
      }; })(c);
      hdr.appendChild(fb); card.appendChild(hdr);
      if(c.org || c.region){ var org = document.createElement('div'); org.className = 'wc-org'; org.textContent = (c.org || '') + (c.region ? ' · ' + c.region : ''); card.appendChild(org); }
      if(c.desc){ var desc = document.createElement('div'); desc.className = 'wc-desc'; desc.textContent = c.desc; card.appendChild(desc); }
      var rows = document.createElement('div'); rows.className = 'wc-rows';
      [['대상', c.target], ['지원', c.support], ['신청', c.how]].forEach(function(r){
        if(r[1]){ var row = document.createElement('div'); row.className = 'wc-row'; var lbl = document.createElement('span'); lbl.className = 'wc-label'; lbl.textContent = r[0]; var val = document.createElement('span'); val.className = 'wc-val'; val.textContent = r[1]; row.appendChild(lbl); row.appendChild(val); rows.appendChild(row); }
      });
      card.appendChild(rows);
      if(c.link){
        var linkRow = document.createElement('div'); linkRow.className = 'wc-link-row';
        var a = document.createElement('a'); a.className = 'wc-link'; a.href = c.link; a.target = '_blank';
        a.innerHTML = '<i class="ti ti-external-link" style="font-size:13px;"></i> 복지로에서 확인하기';
        linkRow.appendChild(a);
        if(c.keyword){
          var kwBox = document.createElement('div'); kwBox.className = 'wc-keyword';
          var kwText = document.createElement('span'); kwText.textContent = '검색창에 "' + c.keyword + '"로 검색해주세요';
          var copyBtn = document.createElement('button'); copyBtn.className = 'wc-copy-btn'; copyBtn.innerHTML = '<i class="ti ti-copy"></i>';
          copyBtn.onclick = (function(kw, btn){ return function(e){
            e.stopPropagation();
            navigator.clipboard.writeText(kw).then(function(){
              btn.innerHTML = '<i class="ti ti-check"></i>';
              setTimeout(function(){ btn.innerHTML = '<i class="ti ti-copy"></i>'; }, 1500);
            });
          };})(c.keyword, copyBtn);
          kwBox.appendChild(kwText); kwBox.appendChild(copyBtn);
          linkRow.appendChild(kwBox);
        }
        card.appendChild(linkRow);
      }
      cards.appendChild(card);
    });
    wrap.appendChild(cards); return wrap;
  }

  function bub(role, text, sv){
    if(sv === undefined) sv = true;
    var area = document.getElementById('chat-area'), em = document.getElementById('empty-state');
    if(em) em.remove();
    var w = document.createElement('div'); w.className = 'msg ' + role;
    var av = document.createElement('div'); av.className = 'avatar ' + role;
    if(role === 'bot'){ var img = document.createElement('img'); img.src = ICON; img.style.cssText = 'width:40px;height:40px;object-fit:contain;'; av.appendChild(img); }else av.textContent = '나';
    var bb = document.createElement('div'); bb.className = 'bubble ' + role;
    if(role === 'bot'){
      try{
        var parsed = JSON.parse(text);
        if(parsed.type === 'cards') { bb.appendChild(renderCards(parsed)); }
        else { bb.innerHTML = (parsed.message || text).split('\n').join('<br>'); }
      }catch(e){ bb.innerHTML = text.split('\n').join('<br>'); }
    }else{ bb.innerHTML = text.split('\n').join('<br>'); }
    w.appendChild(av); w.appendChild(bb); area.appendChild(w); area.scrollTop = area.scrollHeight;
    if(sv && cid){ var s = sess.find(function(x){ return x.id === cid; }); if(s){ s.msgs.push({ role: role, text: text }); if(s.msgs.length === 1){ var title = text; try{ var p = JSON.parse(text); title = p.intro || p.message || text; }catch(e){} s.title = title.slice(0, 18) + (title.length > 18 ? '...' : ''); document.getElementById('topbar-title').textContent = s.title; } save(); rSess(); } }
  }

  function typ(){ var area = document.getElementById('chat-area'); var w = document.createElement('div'); w.className = 'msg bot'; w.id = 'ti'; var av = document.createElement('div'); av.className = 'avatar bot'; var img = document.createElement('img'); img.src = ICON; img.style.cssText = 'width:40px;height:40px;object-fit:contain;'; av.appendChild(img); var bb = document.createElement('div'); bb.className = 'bubble bot'; bb.innerHTML = '<div class="typing"><span></span><span></span><span></span></div>'; w.appendChild(av); w.appendChild(bb); area.appendChild(w); area.scrollTop = area.scrollHeight; }
  function untyp(){ var e = document.getElementById('ti'); if(e) e.remove(); }
  function qk(q){ document.getElementById('msg-input').value = q; send(); }

  async function send(){
    if(!cu){ alert('로그인이 필요합니다.'); return; }
    var inp = document.getElementById('msg-input'), msg = inp.value.trim();
    if(!msg) return; if(!cid) nChat(); inp.value = ''; bub('user', msg); typ();
    try{ var r = await fetch(FLASK + '/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ message: msg, session_id: cid }) }); var d = await r.json(); untyp(); if(d.error){ bub('bot', d.error); return; } bub('bot', d.reply || '답변을 가져오지 못했어요.'); }
    catch(e){ untyp(); bub('bot', '서버에 연결할 수 없습니다.'); }
  }

  async function checkServerSession(){
    try {
      var r = await fetch(FLASK + '/check-session', { credentials: 'include' });
      var d = await r.json();
      if(d.success){
        cu = { username: d.username, role: d.role, region: d.region || '' };
        rUI(); load(); loadF(); rSess();
        if(cid && sess.find(function(s){ return s.id === cid; })) sw(cid);
        else if(sess.length > 0) sw(sess[0].id);
        else nChat();
      } else {
        cu = null; sess = []; cid = null; favs = [];
        document.getElementById('session-list').innerHTML = '';
        document.getElementById('chat-area').innerHTML = '';
        document.getElementById('topbar-title').textContent = '복지 정책 안내 챗봇';
        rUI();
        document.getElementById('login-modal').style.display = 'flex';
      }
    } catch(e) {
      console.error("세션 체크 실패:", e);
      document.getElementById('session-list').innerHTML = '';
      document.getElementById('chat-area').innerHTML = '';
      document.getElementById('login-modal').style.display = 'flex';
    }
  }

  // 시군구 드롭다운
  var regions = {};
  async function loadRegions(){
    try{ var r = await fetch(FLASK + '/regions'); regions = await r.json(); }catch(e){ regions = {}; }
  }
  function fillSgg(sidoId, sggId, selected){
    var sido = document.getElementById(sidoId).value, sel = document.getElementById(sggId);
    var list = regions[sido] || [];
    sel.innerHTML = '';
    var first = document.createElement('option'); first.value = '';
    first.textContent = !sido ? '시/도를 먼저 선택하세요' : (list.length ? '선택 안 함 (시/도 전체)' : '시/군/구 없음');
    sel.appendChild(first);
    list.forEach(function(name){ var o = document.createElement('option'); o.value = name; o.textContent = name; sel.appendChild(o); });
    // 이전 자유 입력값('강남' 등)도 일치하는 항목으로 선택
    if(selected){ var hit = list.find(function(n){ return n === selected || n.slice(0, -1) === selected; }); if(hit) sel.value = hit; }
  }

  // 이벤트 바인딩
  window.onload = function() {
    loadRegions();
    ['reg', 'edit'].forEach(function(p){
      var s = document.getElementById(p + '-sido');
      if(s) s.addEventListener('change', function(){ fillSgg(p + '-sido', p + '-sigungu'); });
    });
    // 세션 확인
    checkServerSession();

    // 버튼 이벤트
    if(document.getElementById('login-btn')) document.getElementById('login-btn').addEventListener('click', doLogin);
    if(document.getElementById('register-btn')) document.getElementById('register-btn').addEventListener('click', doReg);
    if(document.getElementById('new-chat-btn')) document.getElementById('new-chat-btn').addEventListener('click', nChat);
    if(document.getElementById('dark-btn')) document.getElementById('dark-btn').addEventListener('click', tDark);
    if(document.getElementById('logout-btn')) document.getElementById('logout-btn').addEventListener('click', doOut);
    
    if(document.getElementById('go-register')) document.getElementById('go-register').addEventListener('click', showR);
    if(document.getElementById('go-login')) document.getElementById('go-login').addEventListener('click', showL);
    if(document.getElementById('rec-close')) document.getElementById('rec-close').addEventListener('click', function(){ document.getElementById('recommend-modal').style.display = 'none'; });
    if(document.getElementById('rec-btn')) document.getElementById('rec-btn').addEventListener('click', doRec);
    
    if(document.getElementById('fav-open-btn')) document.getElementById('fav-open-btn').addEventListener('click', function(){ loadF(); oFav(); });
    if(document.getElementById('fav-close')) document.getElementById('fav-close').addEventListener('click', function(){ document.getElementById('fav-modal').style.display = 'none'; });
    if(document.getElementById('admin-close')) document.getElementById('admin-close').addEventListener('click', function(){ document.getElementById('admin-modal').style.display = 'none'; });

    // 입력창 이벤트
    if(document.getElementById('msg-input')) document.getElementById('msg-input').addEventListener('keydown', function(e){ if(e.key === 'Enter') send(); });
    if(document.getElementById('send-btn')) document.getElementById('send-btn').addEventListener('click', send);
    
    if(document.getElementById('login-username')) document.getElementById('login-username').addEventListener('keydown', function(e){ if(e.key === 'Enter') doLogin(); });
    if(document.getElementById('login-password')) document.getElementById('login-password').addEventListener('keydown', function(e){ if(e.key === 'Enter') doLogin(); });
    if(document.getElementById('reg-password2')) document.getElementById('reg-password2').addEventListener('keydown', function(e){ if(e.key === 'Enter') doReg(); });

    // 지역 정보 수정
    if(document.getElementById('user-info-area')) {
      document.getElementById('user-info-area').addEventListener('click', function() {
        if (!cu) return;
        var currentRegion = cu.region || "";
        var parts = currentRegion.split(" ");
        var sido = parts[0] || "";
        var sigungu = parts.slice(1).join(" ") || "";
        document.getElementById('edit-sido').value = sido;
        fillSgg('edit-sido', 'edit-sigungu', sigungu);
        document.getElementById('region-modal').style.display = 'flex';
      });
    }

    if(document.getElementById('region-close')) document.getElementById('region-close').addEventListener('click', function() { document.getElementById('region-modal').style.display = 'none'; });
    if(document.getElementById('region-save-btn')) {
      document.getElementById('region-save-btn').addEventListener('click', async function() {
        var sido = document.getElementById('edit-sido').value;
        var sigungu = document.getElementById('edit-sigungu').value.trim();
        var fullRegion = (sido + ' ' + sigungu).trim();
        try {
          var r = await fetch(FLASK + '/update-region', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ region: fullRegion }) });
          var d = await r.json();
          if (d.success) { alert('지역 정보가 정상적으로 수정되었습니다.'); cu.region = fullRegion; document.getElementById('region-modal').style.display = 'none'; nChat(); } 
          else { alert('수정에 실패했습니다: ' + d.message); }
        } catch(e) { alert('서버와 통신 중 오류가 발생했습니다.'); }
      });
    }

    // 모바일 메뉴
    var menuBtn = document.getElementById('mobile-menu-btn');
    var sidebarEl = document.querySelector('.sidebar');
    var overlayEl = document.getElementById('sidebar-overlay');
    if(menuBtn && sidebarEl && overlayEl){
      menuBtn.addEventListener('click', function(){ sidebarEl.classList.toggle('open'); overlayEl.classList.toggle('show'); });
      overlayEl.addEventListener('click', function(){ sidebarEl.classList.remove('open'); overlayEl.classList.remove('show'); });
    }

    if(document.getElementById('logout-confirm-btn')) {
      document.getElementById('logout-confirm-btn').addEventListener('click', function(){
        document.getElementById('logout-modal').style.display = 'none';
        document.getElementById('login-modal').style.display = 'flex';
      });
    }
  };

})();