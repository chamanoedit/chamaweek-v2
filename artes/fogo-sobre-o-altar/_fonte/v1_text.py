import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlayers import render_layers

CREAM = '#EFE5D3'
css = f"""
.cream{{color:{CREAM}}}
#block{{position:absolute;left:0;top:0;width:4800px;height:1350px;display:flex;flex-direction:column;align-items:center;justify-content:center;padding-bottom:70px;box-sizing:border-box}}
#l1{{font-family:PF2;font-variation-settings:'opsz' 420,'wdth' 87.5,'wght' 470;font-size:236px;line-height:1;white-space:nowrap;letter-spacing:-0.004em;position:relative}}
#l1 .em{{font-size:0.40em;margin-left:0.16em;letter-spacing:0.02em}}
#l1 .o2{{position:relative;display:inline-block}}
#gold{{position:absolute;left:50%;top:51%;width:0.27em;height:0.165em;transform:translate(-50%,-50%);background:#D8A63A}}
#l2{{font-family:PF2;font-variation-settings:'opsz' 600,'wdth' 112.5,'wght' 480;font-size:760px;line-height:0.80;white-space:nowrap;letter-spacing:0.015em;position:relative;margin-top:6px}}
#tiny{{position:absolute;left:57.5%;top:49%;font-family:Archivo;font-variation-settings:'wdth' 100,'wght' 700;font-size:31px;line-height:1.12;letter-spacing:0.01em;white-space:nowrap;color:{CREAM};opacity:.82}}
.lab{{position:absolute;font-family:CinzelD;font-size:66px;line-height:1.1;color:{CREAM};white-space:nowrap;opacity:.94}}
#labL{{text-align:right}}
#labR{{text-align:left}}
"""
body = f"""
<div id="block" class="cream">
  <div id="l1" data-layer="title">FOG<span class="o2">O<i id="gold" data-layer="gold"></i></span> SOBRE<span class="em">O</span></div>
  <div id="l2"><div id="tiny" data-layer="tiny">O FOGO ARDERÁ CONTINUAMENTE SOBRE<br>O ALTAR; NÃO SE APAGARÁ. LV 6:13</div><span data-layer="title">ALTAR</span></div>
</div>
<div id="labL" class="lab" data-layer="labels">CULTO RGNR<br>EM CONCERTO</div>
<div id="labR" class="lab" data-layer="labels">LEVÍTICO<br>6:13</div>
"""
script = """
document.fonts.ready.then(()=>{
  const r1=document.getElementById('l1').getBoundingClientRect();
  const r2=document.getElementById('l2').getBoundingClientRect();
  const L=document.getElementById('labL'), R=document.getElementById('labR');
  // optical centre of the cap height of ALTAR (~ baseline - 0.36*fontsize)
  const fs = 760, base = r2.top + 0.5*r2.height + 0.36*fs*0.80;
  const capMid = base - 0.35*fs;
  const top = capMid - 0.5*L.getBoundingClientRect().height;
  L.style.top = top+'px'; R.style.top = top+'px';
  L.style.left = (r2.left - 170 - L.getBoundingClientRect().width) + 'px';
  R.style.left = (r2.right + 170) + 'px';
});
"""
if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/work/layers'
    layers = sys.argv[2].split(',') if len(sys.argv) > 2 else ['all', 'title', 'gold', 'tiny', 'labels']
    print(render_layers('v1', body, css, layers, out, script=script))
