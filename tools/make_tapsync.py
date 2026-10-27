"""Build a tap-sync page per song: press SPACE on each line as you hear it start."""
import json
import pathlib
import html

ROOT = pathlib.Path(r"C:\Users\Dell\Documents\Default Project")
OUT = ROOT / "timing"
OUT.mkdir(exist_ok=True)

TPL = """<!doctype html>
<html><head><meta charset="utf-8"><title>Tap sync — __TITLE__</title>
<style>
 :root{--ink:#0b1220;--cream:#f6e7c8;--ochre:#e8a33d;--teal:#134a4e;--hot:#e0662b}
 *{box-sizing:border-box}
 body{margin:0;background:radial-gradient(120% 90% at 50% 0%,#16323b,#070c18 70%);color:var(--cream);
      font-family:'Segoe UI',system-ui,sans-serif;min-height:100vh}
 header{padding:22px 28px 8px;display:flex;align-items:baseline;gap:16px;flex-wrap:wrap}
 h1{font-size:20px;margin:0;letter-spacing:.02em}
 .meta{opacity:.55;font-size:13px;letter-spacing:.14em;text-transform:uppercase}
 main{display:grid;grid-template-columns:1fr 380px;gap:26px;padding:14px 28px 40px}
 #lines{display:flex;flex-direction:column;gap:6px}
 .row{display:grid;grid-template-columns:74px 1fr;gap:14px;align-items:center;padding:7px 12px;border-left:3px solid transparent;
      border-radius:4px;opacity:.45;transition:.15s}
 .row.done{opacity:.85;border-left-color:var(--teal)}
 .row.active{opacity:1;border-left-color:var(--hot);background:#ffffff0d}
 .row.done .t{color:var(--ochre);font-variant-numeric:tabular-nums}
 .t{font-size:13px;letter-spacing:.06em;color:#8fa3ad;min-width:60px}
 .txt{font-size:19px;line-height:1.25}
 .tr{display:block;font-size:13px;opacity:.55;font-style:italic;margin-top:2px}
 aside{position:sticky;top:18px;align-self:start;background:#0b1220cc;border:1px solid #ffffff14;border-radius:12px;padding:18px}
 audio{width:100%;margin-bottom:14px}
 button{background:var(--ochre);color:#132018;border:0;border-radius:8px;padding:10px 14px;font-weight:700;cursor:pointer;font-size:14px}
 button.ghost{background:#ffffff12;color:var(--cream)}
 .big{font-size:34px;font-variant-numeric:tabular-nums;letter-spacing:.02em;margin:10px 0}
 kbd{background:#ffffff1a;border-radius:4px;padding:1px 6px;font-size:12px}
 .hint{font-size:12.5px;line-height:1.7;opacity:.65}
 .next{font-size:15px;margin-top:8px;color:var(--hot)}
</style></head><body>
<header>
  <h1>Tap sync · __TITLE__</h1>
  <span class="meta">__N__ lines · __DUR__s</span>
</header>
<main>
  <section id="lines"></section>
  <aside>
    <audio id="au" src="__AUDIO__" controls preload="auto"></audio>
    <div class="big" id="clock">0:00.00</div>
    <div class="next" id="next">Next: line 1</div>
    <div style="display:flex;gap:8px;margin:12px 0 16px;flex-wrap:wrap">
      <button id="exp">Export timing JSON</button>
      <button class="ghost" id="undo">Undo</button>
      <button class="ghost" id="reset">Reset</button>
    </div>
    <div class="hint">
      <b>SPACE</b> — stamp start of the next line<br>
      <b>ENTER</b> — play / pause<br>
      <b>BACKSPACE</b> — undo last stamp<br>
      <b>← →</b> — seek 2s<br><br>
      Play from the top, hit <b>SPACE</b> exactly when each line
      begins being sung. Export when done, then drop the file into
      <code>timing/</code> as <code>__ID__.json</code>.
    </div>
  </aside>
</main>
<script>
const LINES = __DATA__;
const au = document.getElementById('au');
const rowsEl = document.getElementById('lines');
const clock = document.getElementById('clock');
const nextEl = document.getElementById('next');
let idx = 0, marks = new Array(LINES.length).fill(null);

rowsEl.innerHTML = LINES.map((l,i)=>`
  <div class="row" id="r${i}">
    <span class="t" id="t${i}">—</span>
    <span class="txt">${l.text.replace(/</g,'&lt;')}${l.translation?`<span class="tr">${l.translation}</span>`:''}</span>
  </div>`).join('');

const fmt = s => `${Math.floor(s/60)}:${String(Math.floor(s%60)).padStart(2,'0')}.${String(Math.floor((s%1)*100)).padStart(2,'0')}`;
function paint(){
  LINES.forEach((_,i)=>{
    const r=document.getElementById('r'+i);
    r.classList.toggle('done', marks[i]!==null);
    r.classList.toggle('active', i===idx);
    document.getElementById('t'+i).textContent = marks[i]===null ? '—' : fmt(marks[i]);
  });
  nextEl.textContent = idx>=LINES.length ? 'All lines stamped ✓' : `Next: line ${idx+1} — “${LINES[idx].text}”`;
  document.getElementById('t'+(idx-1)).scrollIntoView({block:'center',behavior:'smooth'});
}
function stamp(){
  if(idx>=LINES.length) return;
  marks[idx]=au.currentTime; idx++; paint();
}
document.getElementById('exp').onclick=()=>{
  const lines = marks.map((m,i)=>({i, from:m, section:LINES[i].section, key:LINES[i].key}))
                     .filter(x=>x.from!==null);
  const blob=new Blob([JSON.stringify({song:'__ID__',lines},null,1)],{type:'application/json'});
  const a=document.createElement('a'); a.href=URL.createObjectURL(blob);
  a.download='__ID__-taps.json'; a.click();
};
document.getElementById('undo').onclick=()=>{ if(idx>0){idx--;marks[idx]=null;paint();} };
document.getElementById('reset').onclick=()=>{ idx=0; marks.fill(null); paint(); };
addEventListener('keydown',e=>{
  if(e.code==='Space'){ e.preventDefault(); stamp(); }
  else if(e.code==='Enter'){ e.preventDefault(); au.paused?au.play():au.pause(); }
  else if(e.code==='Backspace'){ e.preventDefault(); if(idx>0){idx--;marks[idx]=null;paint();} }
  else if(e.code==='ArrowRight'){ au.currentTime=Math.min(au.duration||0,au.currentTime+2); }
  else if(e.code==='ArrowLeft'){ au.currentTime=Math.max(0,au.currentTime-2); }
});
au.addEventListener('timeupdate',()=>{ clock.textContent=fmt(au.currentTime); });
paint();
</script></body></html>
"""

def main() -> None:
    for p in sorted((ROOT / "lyrics").glob("*.json")):
        song = json.loads(p.read_text(encoding="utf-8"))
        flat = []
        for s in song["sections"]:
            for i, ln in enumerate(s.get("lines", [])):
                flat.append(
                    {
                        "section": s["id"],
                        "key": str(i),
                        "text": ln["text"],
                        "translation": ln.get("translation", ""),
                    }
                )
        page = (
            TPL.replace("__TITLE__", html.escape(song["title"]))
            .replace("__DUR__", str(song["duration"]))
            .replace("__N__", str(len(flat)))
            .replace("__ID__", song["id"])
            .replace("__AUDIO__", "../film/public/" + song["audio"])
            .replace("__DATA__", json.dumps(flat, ensure_ascii=False))
        )
        (OUT / f"tap-sync-{song['id']}.html").write_text(page, encoding="utf-8")
        print("wrote", OUT / f"tap-sync-{song['id']}.html", "lines:", len(flat))


if __name__ == "__main__":
    main()
