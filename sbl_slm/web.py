"""Small loopback-only review server; private text is escaped and phase-gated."""
import html
import json
import secrets
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from .review import Review
from .schema import ValidationError, require


def page(model):
    """Render a readable review workspace while keeping the response phase-gated."""
    context = model.get("X", {})
    x = html.escape(json.dumps(context, ensure_ascii=False, indent=2))
    messages = "".join(f'<article class="message"><div class="meta">{html.escape(str(m.get("speaker", "unknown")))} · {html.escape(str(m.get("created_at", "")))}</div><div>{html.escape(str(m.get("text", "")))}</div></article>' for m in context.get("history", [])) or '<p class="muted">No earlier messages supplied.</p>'
    limits = "".join(f'<li>{html.escape(str(item))}</li>' for item in context.get("limitations", [])) or '<li>None recorded</li>'
    response = html.escape(model.get("observed_response", "")) if "observed_response" in model else "(hidden until phase A is saved)"
    return f'''<!doctype html><meta name="viewport" content="width=device-width,initial-scale=1"><title>Decision review</title>
<style>:root{{--ink:#1d302e;--muted:#61716b;--line:#dce3db;--paper:#f6f7f2;--green:#27664e;font:16px system-ui;color:var(--ink);background:var(--paper)}}*{{box-sizing:border-box}}body{{margin:0}}main{{max-width:1180px;margin:auto;padding:26px clamp(20px,4vw,64px) 50px}}header{{display:flex;justify-content:space-between;gap:16px;margin-bottom:28px;border-bottom:1px solid var(--line);padding-bottom:20px}}h1,h2{{margin:0 0 8px}}h1{{font:500 30px/1.13 Georgia,serif;letter-spacing:-.6px}}h2{{font-size:18px;letter-spacing:-.3px}}.muted,.note{{color:var(--muted)}}.rail{{display:flex;gap:6px;flex-wrap:wrap}}.step{{padding:5px 9px;border-radius:5px;background:#eff2ed;font-size:11px;color:var(--muted)}}.step.active{{background:var(--green);color:white}}.grid{{display:grid;grid-template-columns:minmax(0,1.45fr) minmax(300px,.8fr);gap:20px}}.card{{background:white;border:1px solid var(--line);border-radius:10px;padding:20px;margin-bottom:20px;box-shadow:none}}.message{{border-left:2px solid #98b3a2;padding:10px 12px;margin:10px 0;background:var(--paper);border-radius:0 6px 6px 0}}.meta{{font-size:12px;color:var(--muted);margin-bottom:5px}}pre{{white-space:pre-wrap;word-break:break-word;background:var(--paper);border:0;padding:12px;border-radius:7px;font-size:12px}}label{{display:block;font-weight:600;margin-top:10px}}input,textarea,select,button{{font:inherit;padding:9px 11px;margin-top:5px;border:1px solid var(--line);border-radius:6px;width:100%}}textarea{{min-height:110px;resize:vertical}}button{{width:auto;background:var(--ink);color:white;border-color:var(--ink);cursor:pointer;font-weight:600}}button.secondary{{background:white;color:var(--ink);border-color:var(--line)}}.toolbar{{display:flex;gap:8px;align-items:center;flex-wrap:wrap}}.toolbar button{{width:auto}}.badge{{display:inline-block;padding:3px 7px;border-radius:5px;background:#e8f2e9;color:#286148;border:1px solid #d3e7d6;font-size:10px;font-weight:650}}.hint{{padding:10px;border-radius:6px;background:#e6f0e7;color:#286148;font-size:13px;margin-top:10px}}.success{{color:#17663a;background:#e8f2e9;border-color:#d3e7d6}}.actions{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin-top:8px}}.actions button{{background:white;color:var(--ink);text-align:left;border:1px solid var(--line);margin:0}}.actions button.selected{{background:#e6f0e7;border-color:#98b3a2;color:#286148}}.advanced{{margin-top:12px}}@media(max-width:760px){{main{{padding:20px 16px}}header{{display:block}}.grid{{grid-template-columns:1fr}}}}</style>
<main><header><div><div class="muted">SBL decision-point review</div><h1>Review the next action</h1><p class="note">Reviewer identity is self-declared and unverified · revision <code>{html.escape(model["revision"][:12])}</code></p></div><div class="toolbar"><span class="badge">Draft review</span><button id="copy" class="secondary">Copy revision</button><div class="rail"><span class="step active">1 Context</span><span class="step">2 Target</span><span class="step">3 Reveal</span><span class="step">4 Assess</span></div></div></header><div class="grid"><section><div class="card"><h2>Conversation context</h2><p class="note">Read the available context first. The historical response stays hidden until phase A is saved.</p>{messages}</div><div class="card"><h2>Observed response</h2><pre id="observed">{response}</pre><div class="toolbar"><button id="reveal" class="secondary">Reveal after saving phase A</button><span class="muted">This is irreversible for this reviewer.</span></div></div></section><aside><div class="card"><h2>Case signals</h2><ul>{limits}</ul><details><summary>Technical packet</summary><pre>{x}</pre></details></div><div class="card"><h2>Write your target</h2><p class="note">Step 1: choose the action. Step 2: explain the evidence. Step 3: save before reveal.</p><form id="phase"><label>Reviewer name<input name="actor" placeholder="Your name" required></label><label>Action</label><div class="actions">{''.join(f'<button type="button" data-action="{a}">{a.replace("_", " ")}</button>' for a in ("answer","clarify","qualify","invite_next_step","handoff_human","lookup","wait","stop"))}</div><select name="action" hidden><option>answer</option><option>clarify</option><option>qualify</option><option>invite_next_step</option><option>handoff_human</option><option>lookup</option><option>wait</option><option>stop</option></select><details class="advanced"><summary>Advanced target JSON</summary><textarea name="target" required>{{"action":"wait","arguments":{{"event":""}},"draft":null}}</textarea></details><div class="hint" id="hint">Choose an action, then describe the evidence that supports it.</div><label>Evidence-linked rationale<textarea name="rationale" required></textarea></label><button>Save phase A target</button></form><pre id="status" role="status">No action saved yet.</pre></div></aside></div></main>
<script>const csrf={json.dumps(model["csrf"])};const revision={json.dumps(model["revision"])};const form=document.querySelector('#phase');const status=document.querySelector('#status');const hint=document.querySelector('#hint');const key='sbl-review-'+revision;const hints={{answer:'Resolve the question using cited evidence.',clarify:'Name the missing fact needed to decide.',qualify:'Ask only a permitted, relevant qualification question.',invite_next_step:'Specify the approved destination or next step.',handoff_human:'Name the available human destination.',lookup:'Name the available evidence or tool to retrieve.',wait:'Name the event that must occur before continuing.',stop:'Cite the applicable opt-out or stopping policy.'}};function paintAction(){{let value=form.elements.action.value;document.querySelectorAll('[data-action]').forEach(b=>b.classList.toggle('selected',b.dataset.action===value));hint.textContent=hints[value];}}document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>{{form.elements.action.value=b.dataset.action;paintAction();saveDraft();}});try{{let saved=JSON.parse(localStorage.getItem(key)||'null');if(saved){{for(const [name,value] of Object.entries(saved))if(form.elements[name])form.elements[name].value=value;status.textContent='Local draft restored.';}}}}catch{{}}function saveDraft(){{localStorage.setItem(key,JSON.stringify(Object.fromEntries(new FormData(form))));}}form.addEventListener('input',saveDraft);form.elements.action.onchange=paintAction;paintAction();document.querySelector('#copy').onclick=async()=>{{await navigator.clipboard?.writeText(revision);status.textContent='Revision copied.';}};async function send(path,body){{let r=await fetch(path,{{method:'POST',headers:{{'Content-Type':'application/json','X-CSRF-Token':csrf}},body:JSON.stringify(body)}});let j=await r.json();status.textContent=j.error||JSON.stringify(j);if(!j.error)status.classList.add('success');if(j.observed_response!==undefined)document.querySelector('#observed').textContent=j.observed_response;}}form.onsubmit=e=>{{e.preventDefault();let f=new FormData(form);let target=JSON.parse(f.get('target'));target.action=f.get('action');send('/phase-a',{{revision,actor:f.get('actor'),target,scope:'full',rationale:f.get('rationale')}})}};document.querySelector('#reveal').onclick=()=>{{let actor=form.elements.actor.value;send('/reveal',{{revision,actor}})}};</script>'''


class ReviewHandler(BaseHTTPRequestHandler):
    server_version = "SBLReview/1"

    def _json(self, status, value):
        raw = json.dumps(value, ensure_ascii=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _body(self):
        length = int(self.headers.get("Content-Length", "0"))
        require(0 < length <= 256 * 1024, "invalid_body", "request")
        value = json.loads(self.rfile.read(length))
        require(type(value) is dict, "invalid_body", "request")
        require(secrets.compare_digest(self.headers.get("X-CSRF-Token", ""), self.server.csrf), "csrf_required", "request")
        return value

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/review":
            self._json(404, {"error": "not_found"}); return
        revision = parse_qs(parsed.query).get("revision", [""])[0]
        if not revision:
            self._json(400, {"error": "revision_required"}); return
        try:
            model = self.server.review.view(revision, "web-preview", reveal=False, expected=self.server.review.store.version())
            model = {"revision": revision, "X": model["X"], "csrf": self.server.csrf}
            body = page(model).encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'unsafe-inline'; style-src 'self' 'unsafe-inline'")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers(); self.wfile.write(body)
        except ValidationError as error:
            self._json(400, {"error": error.code})

    def do_POST(self):
        if self.headers.get("Host", "").split(":")[0] not in ("127.0.0.1", "localhost"):
            self._json(403, {"error": "loopback_only"}); return
        try:
            data = self._body(); revision = data.get("revision"); actor = data.get("actor")
            expected = self.server.review.store.version()
            if self.path == "/phase-a":
                self.server.review.phase_a(revision, data["target"], data.get("scope", "full"), data["rationale"], actor, expected)
                self._json(200, {"status": "saved", "phase": "a"})
            elif self.path == "/reveal":
                result = self.server.review.view(revision, actor, reveal=True, expected=expected)
                self._json(200, {"status": "revealed", "observed_response": result["observed_response"]})
            else:
                self._json(404, {"error": "not_found"})
        except (ValidationError, KeyError, ValueError, json.JSONDecodeError) as error:
            self._json(400, {"error": getattr(error, "code", "invalid_request")})

    def log_message(self, *_):
        return


def dispatch(server, method, path, headers=None, body=None):
    """Testable HTTP contract used by the handler; returns status, headers, body."""
    headers = headers or {}
    try:
        if method == "GET":
            parsed = urlparse(path)
            if parsed.path != "/review": return 404, {}, {"error": "not_found"}
            revision = parse_qs(parsed.query).get("revision", [""])[0]
            if not revision: return 400, {}, {"error": "revision_required"}
            model = server.review.view(revision, "web-preview", reveal=False, expected=server.review.store.version())
            return 200, {"Content-Security-Policy": "default-src 'self'; script-src 'unsafe-inline'; style-src 'self' 'unsafe-inline'"}, page({"revision": revision, "X": model["X"], "csrf": server.csrf})
        if headers.get("Host", "").split(":")[0] not in ("127.0.0.1", "localhost"):
            return 403, {}, {"error": "loopback_only"}
        require(secrets.compare_digest(headers.get("X-CSRF-Token", ""), server.csrf), "csrf_required", "request")
        data = body or {}
        revision, actor = data.get("revision"), data.get("actor")
        expected = server.review.store.version()
        if path == "/phase-a":
            server.review.phase_a(revision, data["target"], data.get("scope", "full"), data["rationale"], actor, expected)
            return 200, {}, {"status": "saved", "phase": "a"}
        if path == "/reveal":
            result = server.review.view(revision, actor, reveal=True, expected=expected)
            return 200, {}, {"status": "revealed", "observed_response": result["observed_response"]}
        return 404, {}, {"error": "not_found"}
    except (ValidationError, KeyError, ValueError, json.JSONDecodeError) as error:
        return 400, {}, {"error": getattr(error, "code", "invalid_request")}


class ReviewServer(ThreadingHTTPServer):
    allow_reuse_address = True

    def __init__(self, root, address=("127.0.0.1", 0)):
        require(address[0] in ("127.0.0.1", "localhost"), "loopback_only", "bind")
        super().__init__(address, ReviewHandler)
        self.review = Review(root)
        self.csrf = secrets.token_urlsafe(24)


def serve(root, address=("127.0.0.1", 0)):
    return ReviewServer(root, address)
