import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from textlayers import render_layers
CREAM = '#F4E8D4'
css = f"""
.big{{position:absolute;font-family:Cinzel;font-weight:700;font-size:430px;line-height:1;color:{CREAM};white-space:nowrap;letter-spacing:0.02em}}
.kick{{position:absolute;font-family:Cinzel;font-weight:600;font-size:104px;line-height:1;color:{CREAM};white-space:nowrap;letter-spacing:0.34em}}
.verse{{position:absolute;font-family:Cinzel;font-weight:500;font-size:44px;line-height:1.25;color:{CREAM};white-space:nowrap;letter-spacing:0.16em;opacity:.72}}
"""
body = """
<div id="fogo" class="big" data-layer="title">FOGO</div>
<div id="altar" class="big" data-layer="title">ALTAR</div>
<div id="sobre" class="kick" data-layer="title">SOBRE O</div>
<div id="vl" class="verse" data-layer="verse">O FOGO ARDERÁ CONTINUAMENTE</div>
<div id="vr" class="verse" data-layer="verse">SOBRE O ALTAR; NÃO SE APAGARÁ.</div>
<div id="ref" class="verse" data-layer="verse">LEVÍTICO 6:13</div>
"""
script = """
document.fonts.ready.then(()=>{
  const F=document.getElementById('fogo'), A=document.getElementById('altar'), S=document.getElementById('sobre');
  const VL=document.getElementById('vl'), VR=document.getElementById('vr'), RF=document.getElementById('ref');
  const fs=430, capH=0.70*fs;            // Cinzel cap height ~0.70em
  const baseY = 850;                      // align baseline with altar cornice
  // place: text box top so that baseline = baseY. Cinzel ascent ~ 1.0em box; measure via a probe
  const probe=document.createElement('div'); probe.className='big'; probe.textContent='H'; probe.style.left='0'; probe.style.top='0'; document.body.appendChild(probe);
  const range=document.createRange(); range.selectNodeContents(probe);
  // baseline offset: use an inline-block of zero height aligned to baseline
  const m=document.createElement('span'); m.style.display='inline-block'; m.style.width='1px'; m.style.height='0px'; probe.appendChild(m);
  const baseOff = m.getBoundingClientRect().top - probe.getBoundingClientRect().top;
  probe.remove();
  const top = baseY - baseOff;
  const gap = 210, cx = 2400, altarHalf = 520;
  const fw=F.getBoundingClientRect().width, aw=A.getBoundingClientRect().width;
  F.style.top=top+'px'; A.style.top=top+'px';
  F.style.left=(cx-altarHalf-gap-fw)+'px';
  A.style.left=(cx+altarHalf+gap)+'px';
  // kicker above ALTAR, left aligned with it
  S.style.left=(cx+altarHalf+gap+12)+'px';
  S.style.top=(baseY - capH - 60 - 104*0.86)+'px';
  // verse lines under the big words
  VL.style.top=(baseY+70)+'px'; VR.style.top=(baseY+70)+'px';
  VL.style.left=(cx-altarHalf-gap - VL.getBoundingClientRect().width)+'px';
  VR.style.left=(cx+altarHalf+gap+10)+'px';
  RF.style.top=(baseY+70+58)+'px';
  RF.style.left=(cx+altarHalf+gap+10)+'px';
});
"""
if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/work/layers'
    layers = sys.argv[2].split(',') if len(sys.argv) > 2 else ['all', 'title', 'verse']
    print(render_layers('v2', body, css, layers, out, script=script))
