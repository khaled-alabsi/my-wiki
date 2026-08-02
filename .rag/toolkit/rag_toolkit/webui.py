"""A local search page, served from the standard library.

No framework: one ``http.server`` handler, one embedded HTML page, one JSON endpoint. A
search box over a local index does not justify pulling a web stack into the dependency
tree, and stdlib-only means this works on any machine the toolkit already runs on.

Binds to 127.0.0.1 by default. The index is local and unauthenticated — do not expose it.
"""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>rag search</title>
<style>
 :root{color-scheme:light dark;--bg:#fff;--fg:#111;--mut:#666;--line:#e3e3e3;--acc:#2563eb;--card:#fafafa}
 @media (prefers-color-scheme:dark){:root{--bg:#151517;--fg:#eee;--mut:#999;--line:#2c2c30;--acc:#7aa2f7;--card:#1c1c20}}
 *{box-sizing:border-box}
 body{margin:0;padding:2rem 1rem;background:var(--bg);color:var(--fg);
   font:15px/1.55 ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
 main{max-width:60rem;margin:0 auto}
 h1{font-size:1.1rem;margin:0 0 1rem;font-weight:600}
 h1 small{color:var(--mut);font-weight:400}
 form{display:flex;gap:.5rem;flex-wrap:wrap;margin-bottom:1.25rem}
 input,select{padding:.6rem .7rem;border:1px solid var(--line);border-radius:8px;
   background:var(--bg);color:var(--fg);font:inherit}
 input[name=q]{flex:1 1 22rem}
 button{padding:.6rem 1.1rem;border:0;border-radius:8px;background:var(--acc);color:#fff;
   font:inherit;font-weight:600;cursor:pointer}
 .hit{border:1px solid var(--line);border-radius:10px;padding:.85rem 1rem;margin-bottom:.75rem;
   background:var(--card)}
 .cite{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.82rem;color:var(--acc);
   word-break:break-all}
 .meta{color:var(--mut);font-size:.78rem;margin:.15rem 0 .5rem}
 pre{white-space:pre-wrap;word-wrap:break-word;margin:0;font-size:.86rem;
   font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
 .note{color:var(--mut);font-size:.85rem;margin:.5rem 0}
 .overflow{overflow-x:auto}
</style></head><body><main>
<h1>rag search <small id="sub">loading status…</small></h1>
<form id="f">
  <input name="q" placeholder="search the index…" autofocus autocomplete="off">
  <input name="ext" placeholder=".md,.pdf" size="10">
  <select name="k"><option>5</option><option selected>10</option><option>20</option></select>
  <button>Search</button>
</form>
<div id="notes"></div><div id="out"></div>
</main><script>
const $=s=>document.querySelector(s);
fetch('/api/status').then(r=>r.json()).then(s=>{
  $('#sub').textContent = s.indexed
    ? `${s.files} files · ${s.chunks} chunks · ${(s.embedding||{}).model||''}`
    : 'index is empty — run: rag index';
}).catch(()=>{$('#sub').textContent='status unavailable';});
$('#f').addEventListener('submit',async e=>{
  e.preventDefault();
  const d=new FormData(e.target), q=d.get('q').trim();
  if(!q) return;
  $('#out').innerHTML='<p class="note">searching…</p>'; $('#notes').innerHTML='';
  const p=new URLSearchParams({q,k:d.get('k'),ext:d.get('ext')||''});
  try{
    const r=await fetch('/api/search?'+p), j=await r.json();
    if(j.error){$('#out').innerHTML=`<p class="note">error: ${esc(j.error)}</p>`;return;}
    $('#notes').innerHTML=(j.notes||[]).map(n=>`<p class="note">${esc(n)}</p>`).join('');
    $('#out').innerHTML=(j.hits||[]).length
      ? j.hits.map(h=>`<div class="hit"><div class="cite">${esc(h.citation)}</div>
          <div class="meta">score ${h.score} · ${esc(h.matched_by)}</div>
          <div class="overflow"><pre>${esc(h.text||'')}</pre></div></div>`).join('')
      : '<p class="note">no matches</p>';
  }catch(err){$('#out').innerHTML=`<p class="note">request failed: ${esc(String(err))}</p>`;}
});
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
</script></body></html>"""


def make_handler(rag_dir: Path) -> type[BaseHTTPRequestHandler]:
    from .api import Index

    state: dict[str, Any] = {"index": None}
    guard = threading.Lock()

    def get_index() -> Any:
        with guard:
            if state["index"] is None:
                state["index"] = Index(rag_dir)
            return state["index"]

    class Handler(BaseHTTPRequestHandler):
        server_version = "rag-toolkit"

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, payload: dict[str, Any], code: int = 200) -> None:
            body = json.dumps(payload, default=str).encode("utf-8")
            self._send(code, body, "application/json; charset=utf-8")

        def do_GET(self) -> None:  # noqa: N802 — required by BaseHTTPRequestHandler
            parsed = urlparse(self.path)
            query = parse_qs(parsed.query)
            try:
                if parsed.path in ("/", "/index.html"):
                    self._send(200, PAGE.encode("utf-8"), "text/html; charset=utf-8")
                elif parsed.path == "/api/status":
                    self._json(get_index().status())
                elif parsed.path == "/api/search":
                    self._json(self._search(query))
                else:
                    self._json({"error": "not found"}, 404)
            except Exception as exc:
                self._json({"error": f"{type(exc).__name__}: {exc}"}, 500)

        def _search(self, query: dict[str, list[str]]) -> dict[str, Any]:
            from .retrieve import to_dict

            text = (query.get("q") or [""])[0].strip()
            if not text:
                return {"hits": [], "notes": ["empty query"]}
            k = min(max(int((query.get("k") or ["10"])[0] or 10), 1), 50)
            report = get_index().search_report(
                text, k=k, ext=(query.get("ext") or [""])[0],
                path=(query.get("path") or [""])[0],
                source=(query.get("source") or [""])[0],
            )
            return {
                "query": text,
                "hits": [to_dict(hit, max_chars=1500) for hit in report.hits],
                "notes": report.notes,
                "reranked": report.reranked,
            }

        def log_message(self, fmt: str, *fmt_args: Any) -> None:
            return  # keep the terminal readable; errors still surface in responses

    return Handler


def serve_web(rag_dir: Path, host: str = "127.0.0.1", port: int = 8765) -> int:
    handler = make_handler(Path(rag_dir))
    server = ThreadingHTTPServer((host, port), handler)
    print(f"rag search UI on http://{host}:{port}  (ctrl-c to stop)")
    print(f"workspace: {Path(rag_dir).resolve()}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")
    finally:
        server.server_close()
    return 0
