"""把儀表板 index.html＋資料集包成可直接用瀏覽器開的單一 HTML（d3 走 CDN，dash 以內嵌資料模擬）。"""
import json
import sys
from pathlib import Path

D = Path(__file__).parent
OUT = Path(sys.argv[1])
page = (D / "index.html").read_text(encoding="utf-8")
data = {p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in D.glob("*.json") if p.stem in ("core", "depth", "balls", "fg_threshold", "combo", "cluster")}

TOKENS = """
:root{--color-fg:#1c1b19;--color-fg-muted:#6b6862;--color-bg:#fbfaf7;--color-panel:#ffffff;--color-border-line:#e4e1da;
--color-ok:#2f7d32;--color-warn:#a86a00;--color-bad:#c0392b;--cds-chart-muted:#a8a49c;--cds-chart-grid:#ece9e3;--cds-chart-axis:#c9c5bc;
--cds-chart-reference:#8a867e;--cds-surface-popover:#ffffff;--cds-border:#dcd8d0;--cds-shadow-popover:0 4px 14px rgba(0,0,0,.12);--cds-text-secondary:#6b6862;
--s1:#2a78d6;--s2:#eb6834;--s3:#1baf7a;--s4:#eda100;--s5:#e87ba4;--s6:#008300;--s7:#6250d6;--s8:#e34948}
@media (prefers-color-scheme:dark){:root{--color-fg:#efede8;--color-fg-muted:#a9a59d;--color-bg:#1a1918;--color-panel:#222120;--color-border-line:#3a3835;
--cds-chart-muted:#7d7a74;--cds-chart-grid:#2e2d2b;--cds-chart-axis:#4a4844;--cds-chart-reference:#8f8b84;--cds-surface-popover:#2a2928;--cds-border:#45433f;
--cds-text-secondary:#a9a59d;--s1:#3987e5;--s2:#d95926;color-scheme:dark}}
:root{--font-anthropic-sans:system-ui,-apple-system,"Segoe UI","Noto Sans TC","Microsoft JhengHei",sans-serif;--font-anthropic-serif:Georgia,"Noto Serif TC","PMingLiU",serif;
--cds-font-size-caption:12px;--cds-font-size-body:14px;--cds-font-size-heading:16px;--cds-font-size-title:28px;--cds-font-weight-medium:600;
--cds-gap-xs:4px;--cds-gap-sm:8px;--cds-gap-md:16px;--cds-gap-lg:24px;--cds-pad-xs:4px;--cds-pad-sm:8px;--cds-pad-lg:20px;--cds-radius:8px;--cds-dur-slow:.3s}
body{margin:0;background:var(--color-bg);color:var(--color-fg);font-family:var(--font-anthropic-sans)}
#dash-root{max-width:1200px;margin:0 auto;padding:24px max(16px,env(safe-area-inset-left,0px)) 40px max(16px,env(safe-area-inset-right,0px))}
.dash-skeleton{color:transparent}
"""

SHIM = """
window.dash=(function(){const D=__DATA__,fns=[];
const colors=['var(--s1)','var(--s2)','var(--s3)','var(--s4)','var(--s5)','var(--s6)','var(--s7)','var(--s8)'];
let t;addEventListener('resize',()=>{clearTimeout(t);t=setTimeout(()=>fns.forEach(f=>f()),120)});
return{colors,data:id=>D[id]?{status:'ok',data:D[id],refreshing:false,meta:[]}:{status:'missing',data:[]},
onData:fn=>{fns.push(fn);fn()},setLink:id=>{try{history.replaceState(null,'','#'+id)}catch(e){}},refresh(){},params:()=>({}),setParams(){},resetParams(){}};})();
""".replace("__DATA__", json.dumps(data, ensure_ascii=False))

html = f"""<!doctype html>
<html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zeus 2500 數據報告</title><style>{TOKENS}</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
<script>{SHIM}</script></head>
<body><div id="dash-root">
{page}
</div></body></html>
"""
OUT.write_text(html, encoding="utf-8")
print(OUT, len(html))
