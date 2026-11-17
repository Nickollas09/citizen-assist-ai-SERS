"""
Citizen Assist AI - interface web do módulo de energia (somente biblioteca padrão).

Uso:
    python -m app.web            # abre em http://localhost:8000
    python -m app.web --porta 8080
"""

import argparse
import json
import re
import sys
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from energia.assistente import AssistenteEnergia  # noqa: E402

SESSOES: dict[str, AssistenteEnergia] = {}

PAGINA = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Citizen Assist AI · Energia</title>
<style>
:root{--bg:#f6f7f4;--card:#fff;--txt:#1c2421;--sub:#5a6661;--pri:#1f7a4d;--bot:#eef5f0;--borda:#d8ded9}
@media (prefers-color-scheme:dark){:root{--bg:#121614;--card:#1b211e;--txt:#e9efeb;--sub:#a3b0aa;--pri:#4cc38a;--bot:#1f2a24;--borda:#2c3631}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--txt);font:17px/1.55 system-ui,sans-serif}
main{max-width:760px;margin:0 auto;padding:16px;display:flex;flex-direction:column;min-height:100vh}
h1{font-size:1.3rem;margin:.2rem 0}p.sub{color:var(--sub);margin:0 0 12px}
#chat{flex:1;display:flex;flex-direction:column;gap:10px;padding-bottom:12px}
.msg{padding:12px 14px;border-radius:14px;max-width:92%;white-space:pre-wrap;border:1px solid var(--borda)}
.u{align-self:flex-end;background:var(--pri);color:#fff;border:none}.b{align-self:flex-start;background:var(--bot)}
.atalhos{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.atalhos button{border:1px solid var(--pri);background:var(--card);color:var(--pri);border-radius:999px;padding:8px 12px;font-size:15px;cursor:pointer}
form{display:flex;gap:8px;position:sticky;bottom:0;background:var(--bg);padding:10px 0}
input{flex:1;font-size:17px;padding:12px;border-radius:10px;border:1px solid var(--borda);background:var(--card);color:var(--txt)}
form button{background:var(--pri);color:#fff;border:none;border-radius:10px;padding:0 18px;font-size:17px;cursor:pointer}
</style></head><body><main>
<h1>⚡ Citizen Assist AI · Energia consciente</h1>
<p class="sub">Orientações para reduzir a conta de luz, com fontes e limitações de cada estimativa.</p>
<div class="atalhos" id="atalhos"></div>
<div id="chat" aria-live="polite"></div>
<form id="f"><label for="m" style="position:absolute;left:-9999px">Mensagem</label>
<input id="m" autocomplete="off" placeholder="Ex.: como economizar no chuveiro?"><button>Enviar</button></form>
</main><script>
const chat=document.getElementById('chat'),m=document.getElementById('m');
const atalhos=['Simular minha conta','Como economizar no chuveiro?','Vale a pena placa solar?','Aquecedor solar compensa?','Compare as alternativas','Tarifa Social','Quais as limitações?'];
function md(t){return t.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/\\*\\*(.+?)\\*\\*/g,'<strong>$1</strong>').replace(/\\*(.+?)\\*/g,'<em>$1</em>')}
function add(t,c){const d=document.createElement('div');d.className='msg '+c;d.innerHTML=c==='b'?md(t):md(t);chat.appendChild(d);d.scrollIntoView({behavior:'smooth'})}
async function enviar(t){if(!t.trim())return;add(t,'u');m.value='';
 const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mensagem:t})});
 const j=await r.json();add(j.resposta,'b')}
atalhos.forEach(a=>{const b=document.createElement('button');b.type='button';b.textContent=a;b.onclick=()=>enviar(a);document.getElementById('atalhos').appendChild(b)});
document.getElementById('f').onsubmit=e=>{e.preventDefault();enviar(m.value)};
enviar('oi');
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _sessao(self):
        cookie = self.headers.get("Cookie", "")
        m = re.search(r"sid=([a-f0-9-]{36})", cookie)
        sid = m.group(1) if m and m.group(1) in SESSOES else str(uuid.uuid4())
        SESSOES.setdefault(sid, AssistenteEnergia())
        return sid

    def _enviar(self, codigo, corpo, tipo, sid=None):
        dados = corpo.encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(dados)))
        if sid:
            self.send_header("Set-Cookie", f"sid={sid}; Path=/; HttpOnly; SameSite=Strict")
        self.end_headers()
        self.wfile.write(dados)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._enviar(200, PAGINA, "text/html; charset=utf-8", self._sessao())
        else:
            self._enviar(404, "não encontrado", "text/plain; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/chat":
            return self._enviar(404, "{}", "application/json")
        sid = self._sessao()
        tamanho = min(int(self.headers.get("Content-Length", 0)), 4000)
        try:
            msg = json.loads(self.rfile.read(tamanho) or b"{}").get("mensagem", "")[:500]
        except json.JSONDecodeError:
            msg = ""
        resposta = SESSOES[sid].responder(str(msg))
        self._enviar(200, json.dumps({"resposta": resposta}, ensure_ascii=False),
                     "application/json; charset=utf-8", sid)

    def log_message(self, *args):   # não registra mensagens dos usuários (privacidade)
        pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--porta", type=int, default=8000)
    porta = ap.parse_args().porta
    print(f"Citizen Assist AI · Energia rodando em http://localhost:{porta}  (Ctrl+C para parar)")
    ThreadingHTTPServer(("127.0.0.1", porta), Handler).serve_forever()


if __name__ == "__main__":
    main()
