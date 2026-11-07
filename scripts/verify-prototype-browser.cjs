// Production UI smoke tests with synthetic accounts and intercepted API responses.
// No hosted accounts, email, database, geolocation or Storage requests are made.
// Build frontend first. JOMO_QA_FRONTEND may point to a disposable build copy.
// CHROME_PATH may override the Windows Chrome binary. Run from repository root.
const fs = require('node:fs'), path = require('node:path'), http = require('node:http');
const assert = require('node:assert/strict'), { spawn } = require('node:child_process');
const root = path.resolve(__dirname, '..');
const dir = process.env.JOMO_QA_FRONTEND || path.join(root, 'frontend');
const next = require(path.join(dir, 'node_modules/next'));
const app = next({ dev: false, dir, hostname: '127.0.0.1' });
let server, browser, sid, sequence = 0, buffer = '', origin;
const pending = new Map(), listeners = [], calls = [], errors = [];
function send(method, params = {}, session = sid) {
  return new Promise((resolve, reject) => {
    const id = ++sequence; pending.set(id, { resolve, reject });
    browser.stdio[3].write(JSON.stringify({ id, method, params, ...(session ? { sessionId: session } : {}) }) + '\0');
  });
}
async function evaluate(expression) {
  const result = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
  return result.result.value;
}
async function until(expression, label) {
  const end = Date.now() + 20000;
  while (Date.now() < end) {
    if (await evaluate(expression)) return;
    await new Promise(resolve => setTimeout(resolve, 60));
  }
  throw new Error(label + ': ' + await evaluate('document.body.innerText.slice(-2200)'));
}
async function clickText(text) {
  await until(`Array.from(document.querySelectorAll('button')).some(b=>b.textContent.trim()===${JSON.stringify(text)} && !b.disabled)`, 'enabled button ' + text);
  await evaluate(`Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()===${JSON.stringify(text)}).click()`);
}
async function fillLabel(label, text) {
  const expr = `Array.from(document.querySelectorAll('label')).find(l=>l.textContent.trim().startsWith(${JSON.stringify(label)})).querySelector('input,textarea')`;
  await until(`Array.from(document.querySelectorAll('label')).some(l=>l.textContent.trim().startsWith(${JSON.stringify(label)}) && l.querySelector('input,textarea'))`, 'input ' + label);
  await evaluate(`${expr}.focus()`);
  await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'a', code: 'KeyA', modifiers: 2, windowsVirtualKeyCode: 65 });
  await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'a', code: 'KeyA', modifiers: 2, windowsVirtualKeyCode: 65 });
  await send('Input.insertText', { text });
}
async function checkLabel(label) {
  await evaluate(`Array.from(document.querySelectorAll('label')).find(l=>l.textContent.includes(${JSON.stringify(label)})).querySelector('input[type=checkbox]').click()`);
}
async function navigate(route) {
  await send('Page.navigate', { url: origin + route });
  await until(`document.readyState==='complete' && !document.querySelector('.j-navigation-loader') && !!document.querySelector('h1')`, 'page ready ' + route);
  await until(`!!document.querySelector('input') && Object.keys(document.querySelector('input')).some(k=>k.startsWith('__reactProps')) || ${JSON.stringify(route)}==='/privacy'`, 'hydrated page');
}
const uid = '11111111-1111-4111-8111-111111111111', aid = '22222222-2222-4222-8222-222222222222';
const pid = '33333333-3333-4333-8333-333333333333', proofId = '44444444-4444-4444-8444-444444444444';
const stamp = new Date().toISOString(), today = new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Singapore' }).format(new Date());
const me = { id: uid, display_name: 'Test member', username: 'test_member', created_at: stamp, updated_at: stamp };
const prefs = { user_id: uid, timezone: 'Asia/Singapore', language: 'en', daily_screen_goal_minutes: 120,
  location_enabled: true, screening_enabled: true, notifications_enabled: true, created_at: stamp, updated_at: stamp,
  onboarding_completed_at: null };
const activity = { id: aid, title: 'Synthetic photo walk', description: 'Local QA only', category: 'outdoor', visibility: 'personal',
  status: 'active', created_by: uid, group_id: null, duration_minutes: 10, max_participants: 10, location_required: false,
  proof_requirement: 'photo', max_reward_points: 10, started_at: stamp, ended_at: null, published_at: stamp, created_at: stamp, updated_at: stamp };
const participant = { id: pid, activity_id: aid, user_id: uid, status: 'active', joined_at: stamp, started_at: stamp,
  ended_at: null, completed_at: null, eligible_minutes: 0, points_awarded: 0 };
let records = [], checkin = null, proof = null;
const notices = [{ id: '55555555-5555-4555-8555-555555555555', type: 'friend_request', title: 'Friend request', body: 'A test member sent a request.',
  read_at: null, created_at: stamp, payload: { request_id: '66666666-6666-4666-8666-666666666666', href: '/friends' } }];
function response(request) {
  const url = new URL(request.url), route = url.pathname.replace('/api/v1', ''), method = request.method;
  let body = {}; try { body = JSON.parse(request.postData || '{}'); } catch { /* raw photo body */ }
  calls.push({ route, method, body });
  let data = { success: true, message: 'Saved' }, code = 200, raw = false;
  if (route === '/privacy-notice') { raw = true; data = { organisation: 'Local QA operator', contact_email: 'privacy@example.invalid', photo_retention_days: 7 }; }
  else if (route === '/users/me') { if (method === 'PATCH') Object.assign(me, body); data = me; }
  else if (route === '/users/me/preferences') { if (method === 'PATCH') Object.assign(prefs, body); data = prefs; }
  else if (route === '/users/me/onboarding') prefs.onboarding_completed_at = stamp;
  else if (route === '/users/me/export') data = { users: [me], usage: records, export_scope: 'Synthetic local test' };
  else if (route === '/notifications') data = notices;
  else if (route === '/notifications/read-all') notices.forEach(n => { n.read_at = stamp; });
  else if (/\/friend-requests\/.+\/accept/.test(route)) notices[0].payload.handled = true;
  else if (route === '/friend-requests') data = notices[0].payload.handled ? [] : [{ id: notices[0].payload.request_id, display_name: 'Test friend', sender_id: proofId }];
  else if (['/groups', '/friends', '/group-invitations', '/gardens'].includes(route)) data = [];
  else if (route === '/activities') data = [];
  else if (route === '/activities/' + aid) data = activity;
  else if (route.endsWith('/participants')) data = [participant];
  else if (route.endsWith('/check-ins/me')) { if (method === 'DELETE') checkin = null; else { data = checkin; if (!data) code = 404; } }
  else if (route.endsWith('/check-ins')) { checkin = { check_in_id: proofId, accepted: true, precision: 'coarse', captured_at: stamp, expires_at: new Date(Date.now() + 86400000).toISOString() }; data = checkin; }
  else if (route.endsWith('/end')) { activity.status = 'awaiting_proof'; activity.ended_at = stamp; participant.status = 'awaiting_proof'; participant.ended_at = stamp; participant.eligible_minutes = 10; data = activity; }
  else if (route.endsWith('/proofs/review')) data = [];
  else if (route.endsWith('/proofs/me')) { data = proof; if (!data) code = 404; }
  else if (route.endsWith('/proofs/photo')) { proof = { id: proofId, activity_id: aid, participant_id: pid, proof_type: 'photo', status: 'accepted', submitted_at: stamp, reviewed_at: stamp }; data = proof; }
  else if (route === '/proofs/' + proofId && method === 'DELETE') proof = null;
  else if (route === '/insights/manual') { const entry = { ...body, id: proofId, user_id: uid, created_at: stamp, category_breakdown: { social: body.social_minutes ?? 0, other: body.total_minutes - (body.social_minutes ?? 0) } }; records = [entry]; data = entry; }
  else if (route.startsWith('/insights/records/') && method === 'DELETE') records = [];
  else if (route === '/insights/summary') data = { total_screen_time_minutes: records.reduce((sum, r) => sum + r.total_minutes, 0),
    daily_average_minutes: records[0]?.total_minutes ?? 0, social_time_minutes: records[0]?.social_minutes ?? 0,
    start_date: url.searchParams.get('from') || today, end_date: url.searchParams.get('to') || today, days_recorded: records.length, daily_breakdown: records };
  else if (route === '/ai/wellbeing/recommendation') data = { headline: 'A fresh moment', suggestion: 'Try a short walk.', category: 'outdoor' };
  else if (route === '/ai/privacy/text') data = { status: 'completed', has_potential_pii: true, has_harmful_content_indicators: false,
    detections: [{ entity_type: 'EMAIL_ADDRESS', start: 6, end: 26, score: 1, category: 'contact' }], redacted_text: 'Email <EMAIL_ADDRESS>', limitations: ['Automated screening can miss information.'], engine: 'presidio', ner_enabled: true };
  else if (!['/users/me/proof-images', '/users/me/screening-history'].includes(route)) throw new Error('Unmocked route ' + method + ' ' + route);
  return { code, result: raw ? data : { data: code === 404 ? null : data, request_id: 'local-browser-qa', ...(code === 404 ? { error: { code: 'NOT_FOUND', message: 'No saved evidence.' } } : {}) } };
}
const timeout = setTimeout(() => { browser?.kill(); server?.close(); console.error('Browser QA timed out'); process.exit(1); }, 150000);
(async () => { try {
  await app.prepare(); server = http.createServer(app.getRequestHandler());
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve)); origin = 'http://127.0.0.1:' + server.address().port;
  const out = path.join(dir, '.next', 'prototype-browser-qa'); fs.mkdirSync(out, { recursive: true });
  browser = spawn(process.env.CHROME_PATH || 'C:/Program Files/Google/Chrome/Application/chrome.exe', ['--headless=new', '--no-sandbox', '--disable-gpu', '--no-first-run', '--remote-debugging-pipe', '--user-data-dir=' + path.join(out, 'profile-' + Date.now())], { windowsHide: true, stdio: ['ignore', 'ignore', 'ignore', 'pipe', 'pipe'] });
  browser.stdio[4].on('data', data => {
    buffer += data.toString(); let index;
    while ((index = buffer.indexOf('\0')) >= 0) {
      const raw = buffer.slice(0, index); buffer = buffer.slice(index + 1); if (!raw) continue;
      const msg = JSON.parse(raw);
      if (msg.id) { const item = pending.get(msg.id); if (item) { pending.delete(msg.id); msg.error ? item.reject(new Error(JSON.stringify(msg.error))) : item.resolve(msg.result); } }
      else listeners.forEach(listener => listener(msg));
    }
  });
  const target = await send('Target.createTarget', { url: 'about:blank' }, null);
  sid = (await send('Target.attachToTarget', { targetId: target.targetId, flatten: true }, null)).sessionId;
  listeners.push(msg => {
    if (msg.method === 'Page.javascriptDialogOpening') void send('Page.handleJavaScriptDialog', { accept: true });
    if (msg.method === 'Runtime.exceptionThrown') errors.push(JSON.stringify(msg.params.exceptionDetails));
    if (msg.method !== 'Fetch.requestPaused') return;
    let result; try { result = response(msg.params.request); } catch (error) { errors.push(error.message); result = { code: 500, result: {} }; }
    void send('Fetch.fulfillRequest', { requestId: msg.params.requestId, responseCode: result.code,
      responseHeaders: [{ name: 'Content-Type', value: 'application/json' }, { name: 'Cache-Control', value: 'no-store' }],
      body: Buffer.from(JSON.stringify(result.result)).toString('base64') });
  });
  await send('Page.enable'); await send('Runtime.enable');
  await send('Fetch.enable', { patterns: [{ urlPattern: '*://*/api/v1/*' }] });
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 1100, deviceScaleFactor: 1, mobile: false });
  await send('Emulation.setGeolocationOverride', { latitude: 1.3521, longitude: 103.8198, accuracy: 30 });
  await send('Browser.grantPermissions', { origin, permissions: ['geolocation'] }, null);
  await send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: out }, null);
  const token = Buffer.from('{}').toString('base64url') + '.' + Buffer.from(JSON.stringify({ sub: uid })).toString('base64url') + '.local';
  await send('Page.addScriptToEvaluateOnNewDocument', { source: `localStorage.setItem('jomo_auth_token',${JSON.stringify(token)});localStorage.setItem('jomo_token_expires_at',String(Date.now()+3600000));localStorage.setItem('jomo:privacy-challenge:last-shown:${uid}',String(Date.now()));` });
  await navigate('/insights');
  await until(`document.body.innerText.includes('Make this your space')`, 'onboarding form');
  await fillLabel('Display name', 'Alex Garden'); await checkLabel('I have read the privacy notice.'); await clickText('Save and begin');
  await until(`!document.body.innerText.includes('Make this your space') && document.querySelector('.j-account-name strong').textContent==='Alex Garden'`, 'onboarding saved and greeting refreshed');
  assert.equal(calls.find(c => c.route === '/users/me/onboarding').body.privacy_notice_acknowledged, true);
  console.log('PASS: Onboarding acknowledgement saves preferences and refreshes the display-name greeting.');
  await fillLabel('Total hours', '2'); await fillLabel('Total minutes', '15'); await fillLabel('Social minutes', '30'); await clickText('Save screen time');
  await until(`!!document.querySelector('.j-saved-row') && document.body.innerText.includes('Saved 2h 15m')`, 'saved screen-time receipt and table');
  assert.equal(records[0].total_minutes, 135); assert.equal(records[0].social_minutes, 30);
  await evaluate(`Array.from(document.querySelectorAll('a')).find(a=>a.textContent==='Edit').click()`);
  await fillLabel('Total hours', '1'); await clickText('Save screen time');
  await until(`document.querySelector('.j-saved-row').textContent.includes('1h 15m')`, 'screen-time edit');
  await clickText('Delete'); await until(`document.body.innerText.includes('No screen time recorded in this window.')`, 'screen-time deletion');
  console.log('PASS: Manual screen time visibly saves, edits and deletes without adding offline minutes.');
  await evaluate(`document.querySelector('.j-notifications').open=true`); await clickText('Accept friend');
  await until(`!Array.from(document.querySelectorAll('button')).some(b=>b.textContent==='Accept friend')`, 'notification action resolves');
  await clickText('Mark all as read'); await until(`document.querySelector('.j-notifications summary').getAttribute('aria-label').includes('0 unread')`, 'mark notices read');
  console.log('PASS: Notification actions and unread count update in the website.');
  await navigate('/activities/' + aid);
  await checkLabel('I agree to share one approximate location'); await clickText('Share one check-in');
  await until(`document.body.innerText.includes('Check-in recorded')`, 'one-time check-in receipt');
  const locationCall = calls.find(c => c.route.endsWith('/check-ins') && c.method === 'POST'); assert.equal(locationCall.body.consent, true);
  await clickText('Remove my check-in'); await until(`!document.body.innerText.includes('Check-in recorded')`, 'check-in removal');
  await clickText('End activity for participants'); await until(`document.body.innerText.toLowerCase().includes('awaiting proof')`, 'activity ended');
  // A synthetic image fixture is generated by the Python verification setup.
  const photoPath = process.env.JOMO_QA_PHOTO; assert.ok(photoPath && fs.existsSync(photoPath), 'Set JOMO_QA_PHOTO to a synthetic JPEG.');
  const doc = await send('DOM.getDocument'); const input = await send('DOM.querySelector', { nodeId: doc.root.nodeId, selector: 'input[type=file]' });
  await send('DOM.setFileInputFiles', { nodeId: input.nodeId, files: [photoPath] });
  await until(`!!document.querySelector('img[alt="Your selected activity photo, not yet uploaded"]')`, 'local photo preview');
  await checkLabel('I have read the photo notice'); await clickText('Upload and submit photo');
  await until(`document.body.innerText.includes('Your evidence: accepted')`, 'photo upload receipt');
  assert.ok(calls.some(c => c.route.endsWith('/proofs/photo') && c.method === 'POST'));
  await clickText('Remove my evidence'); await until(`!document.body.innerText.includes('Your evidence: accepted')`, 'evidence removal');
  console.log('PASS: Explicit one-time location consent/removal and photo preview/upload/removal work in Chrome.');
  await navigate('/settings'); await clickText('Download my data');
  await until(`document.body.innerText.includes('Your account-data download is ready.')`, 'account export');
  await clickText('Remove my proof photos'); await until(`document.body.innerText.includes('Photo access removed;')`, 'photo withdrawal');
  await clickText('Clear screening history'); await until(`document.body.innerText.includes('Screening history cleared.')`, 'screening history removal');
  console.log('PASS: Settings exports account data and submits both privacy deletion controls.');
  await navigate('/privacy-guardian'); await fillLabel('Text to check', 'Email person@example.invalid');
  await checkLabel('I agree to send this text'); await clickText('Check for personal information');
  await until(`document.querySelector('.j-output')?.textContent==='Email <EMAIL_ADDRESS>'`, 'redacted draft');
  assert.equal(calls.find(c => c.route === '/ai/privacy/text').body.consent, true);
  console.log('PASS: Guardian submits explicit consent and renders the redacted draft as text.');
  await send('Emulation.setDeviceMetricsOverride', { width: 390, height: 844, deviceScaleFactor: 1, mobile: true });
  await navigate('/privacy'); await until(`document.body.innerText.includes('Local QA operator')`, 'public configured privacy notice');
  assert.ok(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'), 'Mobile privacy notice must fit viewport');
  const screenshot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  fs.writeFileSync(path.join(out, 'privacy-mobile.png'), Buffer.from(screenshot.data, 'base64'));
  await navigate('/insights');
  await until(`!!document.querySelector('#screen-time-form')`, 'mobile Insights form');
  assert.ok(await evaluate('document.documentElement.scrollWidth<=innerWidth+1'), 'Mobile Insights must fit viewport');
  const insightsShot = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  fs.writeFileSync(path.join(out, 'insights-mobile.png'), Buffer.from(insightsShot.data, 'base64'));
  assert.deepEqual(errors, []); console.log('PASS: Public privacy notice works on mobile; no uncaught browser errors.');
  await send('Browser.close', {}, null);
} finally { clearTimeout(timeout); browser?.kill(); await new Promise(resolve => server ? server.close(resolve) : resolve()); await app.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
