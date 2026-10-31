import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlayers import render_layers
css = """
#t{position:absolute;left:0;width:4800px;text-align:center;font-family:Anton;font-size:500px;line-height:1;color:#fff;white-space:nowrap;letter-spacing:0.035em}
#ref{position:absolute;left:0;width:4800px;text-align:center;font-family:Archivo;font-variation-settings:'wdth' 100,'wght' 600;font-size:40px;letter-spacing:0.62em;color:#F3E2C8;white-space:nowrap}
"""
body = """
<div id="t" data-layer="title">FOGO SOBRE O ALTAR</div>
<div id="ref" data-layer="ref">LEVÍTICO 6:13</div>
"""
script = """
document.fonts.ready.then(()=>{
  const t=document.getElementById('t');
  const m=document.createElement('span'); m.style.display='inline-block'; m.style.width='1px'; m.style.height='0px'; t.appendChild(m);
  t.style.top='0px';
  const baseOff = m.getBoundingClientRect().top - t.getBoundingClientRect().top;
  const baseY = 1040;
  t.style.top = (baseY - baseOff) + 'px';
  const r=document.getElementById('ref'); r.style.top=(baseY+70)+'px'; r.style.paddingLeft='0.62em';
});
"""
if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/work/layers'
    layers = sys.argv[2].split(',') if len(sys.argv) > 2 else ['title', 'ref']
    print(render_layers('v3', body, css, layers, out, script=script))
