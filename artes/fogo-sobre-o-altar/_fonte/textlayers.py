"""Render typography layers (transparent PNG, full res) with headless Chromium."""
import subprocess, os, sys
SHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shot.js')
FONTS = os.environ.get('FONTS_DIR', '/tmp/fonts')

FONT_CSS = f"""
@font-face{{font-family:PF2;src:url('file://{FONTS}/Playfair[opsz,wdth,wght].ttf')}}
@font-face{{font-family:CinzelD;src:url('file://{FONTS}/CinzelDecorative-Regular.ttf')}}
@font-face{{font-family:CinzelDB;src:url('file://{FONTS}/CinzelDecorative-Bold.ttf')}}
@font-face{{font-family:Cinzel;src:url('file://{FONTS}/Cinzel[wght].ttf')}}
@font-face{{font-family:Archivo;src:url('file://{FONTS}/Archivo[wdth,wght].ttf')}}
@font-face{{font-family:Anton;src:url('file://{FONTS}/Anton-Regular.ttf')}}
@font-face{{font-family:Cormorant;src:url('file://{FONTS}/CormorantGaramond[wght].ttf')}}
html,body{{margin:0;padding:0;background:transparent;overflow:hidden}}
"""


def render_layers(name, body_html, css, layers, outdir, w=4800, h=1350, script=''):
    os.makedirs(outdir, exist_ok=True)
    outs = {}
    for L in layers:
        vis = '' if L == 'all' else f'[data-layer]{{visibility:hidden}} [data-layer~="{L}"]{{visibility:visible}}'
        html = f"""<!doctype html><html><head><meta charset="utf-8"><style>{FONT_CSS}
body{{width:{w}px;height:{h}px;position:relative}}
{css}
{vis}
</style></head><body>{body_html}<script>{script}</script></body></html>"""
        hp = os.path.join(outdir, f'{name}_{L}.html'); op = os.path.join(outdir, f'{name}_{L}.png')
        open(hp, 'w', encoding='utf-8').write(html)
        subprocess.run(['node', SHOT, hp, op, str(w), str(h), '1'], check=True)
        outs[L] = op
    return outs
