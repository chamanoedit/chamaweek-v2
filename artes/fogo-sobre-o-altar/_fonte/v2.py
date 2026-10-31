"""V2 — Altar de pedra com chifres, fogo vivo, tipografia romana (Cinzel)."""
import sys, os, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw
from fx import *
from fire import fire_noise, flame

T = 10.0
FPS = 30
LAYERS = os.environ.get('LAYERS', '/tmp/work/layers')
CX = 2400


def bbox(a, pad=0):
    ys, xs = np.nonzero(a > 0.004)
    return max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + 1 + pad, ys.max() + 1 + pad


def quad(p0, c, p1, n=24):
    t = np.linspace(0, 1, n)[:, None]
    return ((1 - t) ** 2 * np.array(p0) + 2 * (1 - t) * t * np.array(c) + t ** 2 * np.array(p1)).tolist()


def horn(xb0, xb1, yb, xt, yt, lean):
    left = quad((xb0, yb), (xb0 + lean * 0.3, yb - 0.55 * (yb - yt)), (xt, yt))
    right = quad((xt + 6, yt + 4), (xb1 + lean * 0.15, yb - 0.45 * (yb - yt)), (xb1, yb))
    return [tuple(p) for p in left + right]


class Altar:
    """Static altar render at full-res units * s, inside box AX0..AX1, AY0..AY1."""
    def __init__(self, s, rng):
        self.s = s
        AX0, AY0, AX1, AY1 = 1780, 660, 3020, 1350
        self.box = (AX0, AY0, AX1, AY1)
        w = int(round((AX1 - AX0) * s)); h = int(round((AY1 - AY0) * s))
        SS = 4
        def mask(polys):
            im = Image.new('L', (w * SS, h * SS), 0); d = ImageDraw.Draw(im)
            for P in polys:
                d.polygon([((x - AX0) * s * SS, (y - AY0) * s * SS) for x, y in P], fill=255)
            return np.asarray(im.resize((w, h), Image.BOX)).astype(np.float32) / 255.0
        R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        X = AX0 + (xx + 0.5) / s; Y = AY0 + (yy + 0.5) / s
        self.X, self.Y = X, Y
        m_pl_top = mask([R(1880, 1238, 2920, 1252)])
        m_pl = mask([R(1866, 1252, 2934, 1302)])
        m_body = mask([R(1920, 905, 2880, 1240)])
        m_cor_top = mask([R(1893, 848, 2907, 862)])
        m_cor = mask([R(1884, 862, 2916, 906)])
        m_top = mask([R(1905, 830, 2895, 849)])
        HF = horn(1886, 1990, 852, 1904, 752, -30); HB = horn(1938, 2008, 834, 1950, 768, -20)
        m_hfl = mask([HF])
        m_hfr = mask([[(2*CX - x, y) for x, y in HF]])
        m_hbl = mask([HB])
        m_hbr = mask([[(2*CX - x, y) for x, y in HB]])
        # rough stone texture (static fbm)
        def fbm(scales, amps, seed):
            r = np.random.default_rng(seed); acc = np.zeros((h, w), np.float32)
            for sc, am in zip(scales, amps):
                nz = r.standard_normal((h, w)).astype(np.float32)
                nz = blur(nz, sc * s); nz /= max(nz.std(), 1e-6); acc += am * nz
            return acc / sum(amps)
        tex = fbm((1.2, 3.5, 10, 28), (0.35, 0.4, 0.5, 0.45), 21)
        tex2 = fbm((2.0, 7.0), (0.5, 0.5), 22)
        # blocks on body: 3 courses
        mortar = np.zeros((h, w), np.float32); bevel_hi = np.zeros((h, w), np.float32); bevel_lo = np.zeros((h, w), np.float32)
        blockval = np.ones((h, w), np.float32)
        r = np.random.default_rng(5)
        def blocks(x0, x1, y0, y1, minw, maxw, off):
            nonlocal mortar, bevel_hi, bevel_lo, blockval
            xs = [x0]; x = x0 + off
            while x < x1 - minw * 0.6:
                xs.append(x); x += r.uniform(minw, maxw)
            xs.append(x1)
            for a, b in zip(xs[:-1], xs[1:]):
                inb = (X >= a) & (X < b) & (Y >= y0) & (Y < y1)
                blockval[inb] = r.uniform(0.75, 1.2)
                # bevel: distance to edges
                dt = np.clip(Y - y0, 0, None); db = np.clip(y1 - Y, 0, None); dl = np.clip(X - a, 0, None); dr = np.clip(b - X, 0, None)
                bevel_hi[inb] = np.maximum(np.exp(-dt[inb] / 7.0), 0.5 * np.exp(-dl[inb] / 6.0))[...]
                bevel_lo[inb] = np.maximum(np.exp(-db[inb] / 9.0), 0.6 * np.exp(-dr[inb] / 7.0))
                # mortar joints (irregular)
                jitter = tex2 * 2.5
                for xe in (a, b):
                    mortar = np.maximum(mortar, np.exp(-((X - xe + jitter) / 4.0) ** 2) * inb)
                for ye in (y0, y1):
                    mortar = np.maximum(mortar, np.exp(-((Y - ye + jitter) / 3.6) ** 2) * inb)
        ch = (1240 - 905) / 3
        for i in range(3):
            blocks(1920, 2880, 905 + i * ch, 905 + (i + 1) * ch, 170, 300, [95, 205, 140][i])
        blocks(1884, 2916, 862, 906, 330, 520, 240)
        blocks(1866, 2934, 1252, 1302, 360, 560, 170)
        # chips / cracks (dark speckles)
        crack = np.clip((fbm((1.0, 2.5), (0.6, 0.4), 23) - 1.6) * 1.2, 0, 1)
        front = np.clip(m_body + m_cor + m_pl, 0, 1)
        tops = np.clip(m_cor_top + m_pl_top, 0, 1)
        horns_f = np.clip(m_hfl + m_hfr, 0, 1); horns_b = np.clip(m_hbl + m_hbr, 0, 1)
        self.front_mask = np.clip(front + tops + horns_f, 0, 1)   # occludes fire behind
        self.all_mask = np.clip(self.front_mask + horns_b + m_top, 0, 1)
        self.top_mask = m_top
        albedo = np.array([0.20, 0.165, 0.14], np.float32)
        rough = (1 + 0.32 * tex)[..., None]
        base = albedo * rough * blockval[..., None] * (1 - 0.55 * mortar[..., None]) * (1 - 0.6 * crack[..., None])
        # lighting from the fire above (warm) + faint cool ambient
        dist_c = np.abs(X - CX) / 560.0
        L_front = (0.48 * np.exp(-(Y - 858) / 150.0) + 0.05) * (1.0 - 0.32 * dist_c ** 2)
        L_front = L_front * (1 + 0.9 * bevel_hi) * (1 - 0.55 * bevel_lo)
        L_top = np.where(Y < 900, 1.1 * (1 - 0.35 * dist_c ** 2), 0.10)
        lit = np.where(tops > 0.5, L_top, L_front)
        # horns: rim light on the side facing the fire + top
        inner = np.clip(1 - np.abs(X - CX) / 560.0, 0, 1)
        Lh = 0.25 + 1.4 * smoothstep(0.80, 1.0, 1 - np.abs(np.abs(X - CX) - 452) / 70.0) * 0 + 0.0
        hx_rim = np.clip(((np.abs(X - CX) < 520) * 1.0), 0, 1)
        # build per-horn rim: brighter toward the centre side
        rim = np.zeros((h, w), np.float32)
        k = max(1, int(round(9 * s)))
        for mk, sign in ((m_hfl, 1), (m_hfr, -1), (m_hbl, 1), (m_hbr, -1)):
            inward = np.roll(mk, -sign * k, axis=1)          # neighbour toward the fire
            up = np.roll(mk, k, axis=0)                       # neighbour above
            edge_in = np.clip(mk - inward, 0, 1); edge_up = np.clip(mk - up, 0, 1)
            edge = blur(np.clip(edge_in * 1.0 + edge_up * 0.7, 0, 1), 2.5 * s)
            body = mk * 0.012 * (1 + 0.3 * tex)
            rim += body + mk * edge * 0.55
        lit = lit * (1 - horns_f - horns_b).clip(0, 1) + rim
        warm = np.array([1.0, 0.46, 0.16], np.float32)
        amb = np.array([0.010, 0.012, 0.016], np.float32)
        self.rad_lit = base * lit[..., None] * warm * 0.95           # scales with flicker
        self.rad_amb = base * amb * 2.0 + 0.0
        # glowing coals on the top surface
        coal = np.clip(0.5 + 0.6 * fbm((1.5, 4.0, 9.0), (0.4, 0.4, 0.3), 24), 0, 1.5)
        self.coal = coal * m_top * (1 - smoothstep(380, 470, np.abs(X - CX)))
        # floor glow strip
        self.alpha = self.all_mask[..., None]

    def render(self, fl, coal_n):
        rad = self.rad_amb + self.rad_lit * fl
        coal = (self.coal * (0.6 + 0.5 * coal_n))[..., None] * np.array([2.2, 0.55, 0.06], np.float32)
        return rad + coal


class V2:
    def __init__(self, s):
        self.s = s
        w, h = int(round(W * s)), int(round(H * s)); self.w, self.h = w, h
        self.bs = bs = s * 0.5
        bw, bh = int(round(W * bs)), int(round(H * bs)); self.bw, self.bh = bw, bh
        yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
        X = (xx + 0.5) / bs; Y = (yy + 0.5) / bs
        self.nv = NoiseVol(N=256, D=32, kc=14, ktc=2.5, seed=31)
        self.nv2 = NoiseVol(N=128, D=16, kc=6, ktc=1.5, seed=32)
        bg = np.zeros((bh, bw, 3), np.float32) + np.array([0.0022, 0.0018, 0.0017], np.float32)
        glow = np.exp(-(((X - CX) / 1350) ** 2 + ((Y - 560) / 620) ** 2))
        bg += glow[..., None] * np.array([0.030, 0.0085, 0.0018], np.float32)
        glow2 = np.exp(-(((X - CX) / 2600) ** 2 + ((Y - 700) / 900) ** 2))
        bg += glow2[..., None] * np.array([0.005, 0.0015, 0.0005], np.float32)
        # floor
        floor = smoothstep(1296, 1312, Y)
        fglow = np.exp(-(((X - CX) / 1500) ** 2)) * (0.6 + 0.4 * smoothstep(1300, 1350, Y))
        fshadow = 1 - 0.75 * np.exp(-(((X - CX) / 600) ** 6)) * smoothstep(1290, 1340, Y) * 0.0
        bg += (floor * fglow)[..., None] * np.array([0.035, 0.011, 0.0035], np.float32)
        self.bg = bg
        self.vig = vignette(bh, bw, strength=0.62, power=1.8)[..., None]
        # smoke column mask
        widen = 420 + np.clip(850 - Y, 0, None) * 0.9
        self.smask = (np.exp(-((X - CX) / widen) ** 2) * smoothstep(-200, 500, Y) * (1 - smoothstep(600, 860, Y)))
        self.smask2 = smoothstep(1350, 200, Y) * 0.35 * (1 - np.exp(-((X - CX) / 700) ** 2))
        self.sx = (X * 0.020).astype(np.float32); self.sy = (Y * 0.016).astype(np.float32)
        # fire region (half of output res)
        self.fs = fs = s * 0.5
        FX0, FY0, FX1, FY1 = 1700, 0, 3100, 870
        self.fbox = (FX0, FY0, FX1, FY1)
        self.FX, self.FY = grid(FX0, FY0, FX1, FY1, fs)
        u = (self.FX - CX) / 520.0
        self.fu = u
        r0 = np.random.default_rng(8)
        bumps = np.zeros_like(self.FX)
        for k in range(6):
            c0 = CX + (r0.random() - 0.5) * 760; wd = 70 + 120 * r0.random(); am = 0.15 + 0.3 * r0.random()
            bumps += am * np.exp(-((self.FX - c0) / wd) ** 2)
        self.fprof = (0.22 + 0.78 * np.cos(np.clip(u, -1.25, 1.25) * np.pi / 2.5) ** 2.0) * (0.95 + bumps)
        self.ftop = smoothstep(20, 230, self.FY)
        self.fv = (846 - self.FY) / 545.0
        self.core_prof = 0.30 + 0.20 * np.cos(np.clip(u, -1.3, 1.3) * np.pi / 2.6)
        # altar (full output res)
        self.altar = Altar(s, np.random.default_rng(1))
        AX0, AY0, AX1, AY1 = self.altar.box
        self.abox = (int(round(AX0 * s)), int(round(AY0 * s)))
        # particles
        def spawn_fire(R):
            return CX + (R[:, 0] - 0.5) * 900, 820 - R[:, 5] * 380
        self.emb_s = Embers(300, T, 41, spawn_fire, life_m=(1, 2, 3), speed=(140, 380), drift=90, streak=0.06, bright=(0.9, 3.2))
        self.emb_m = Embers(70, T, 42, spawn_fire, life_m=(1, 2), speed=(110, 260), drift=150, streak=0.05, bright=(0.6, 1.8))
        def spawn_wide(R):
            return CX + (R[:, 0] - 0.5) * 3600, 1250 + R[:, 5] * 200
        self.emb_w = Embers(90, T, 43, spawn_wide, life_m=(1,), speed=(60, 150), drift=90, streak=0.05, bright=(0.4, 1.4))
        self.tone = ToneLUT(exposure=1.15)
        # typography
        Lr = lambda n: load_rgba(f'{LAYERS}/v2_{n}.png', w, h)
        title, ta = Lr('title'); verse, va = Lr('verse')
        allA = np.maximum(ta, va)[..., 0]
        self.text_boxes = []
        # split in left / right halves to keep the bboxes tight
        for xa, xb in ((0, w // 2), (w // 2, w)):
            sub = allA[:, xa:xb]
            x0, y0, x1, y1 = bbox(sub, pad=int(70 * s)); x0 += xa; x1 += xa
            sl = (slice(y0, y1), slice(x0, x1))
            ty, tx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
            TX = (tx + 0.5) / s; TY = (ty + 0.5) / s
            near = 1.0 / (1.0 + ((np.abs(TX - CX) - 700) / 900).clip(0) ** 2)
            vert = smoothstep(500, 860, TY)
            lightk = (0.25 + 0.75 * near) * (0.85 + 0.15 * vert)
            warm = np.array([1.0, 0.80, 0.55], np.float32)
            gold = np.array([0.98, 0.80, 0.52], np.float32)
            vg = smoothstep(560, 860, TY)[..., None]
            cA = title[sl] * (1 - 0.40 * vg) + gold * 0.40 * vg * (title[sl] > 0).astype(np.float32)
            cA = cA * 0.94
            cB = (lightk[..., None] * 0.22) * (np.array([1.0, 0.86, 0.66], np.float32) - cA)
            shadow = blur(ta[..., 0], 26 * s)[sl][..., None]
            g = blur(ta[..., 0], 40 * s)[sl][..., None] * (near[..., None] * np.array([0.30, 0.13, 0.04], np.float32))
            self.text_boxes.append(dict(sl=sl, ta=ta[sl], va=va[sl], verse=verse[sl], cA=cA, cB=cB, shadow=shadow, glow=g))
        self.rng = np.random.default_rng(99)
        self.grain_size = 1.2

    def flicker(self, t):
        p = TAU * t / T
        return 1 + 0.08 * np.sin(4 * p + 0.4) + 0.06 * np.sin(9 * p + 1.9) + 0.04 * np.sin(17 * p + 4.1) + 0.025 * np.sin(29 * p + 2.2)

    def frame(self, t, grain_amt=0.03):
        s, w, h, bs = self.s, self.w, self.h, self.bs
        fl = self.flicker(t); ph = t / T
        img = self.bg * (0.9 + 0.1 * fl)
        # smoke (half res)
        sm = self.nv2.sample(ph * self.nv2.D, self.sx + 0.0, self.sy + ph * 128 * 2)
        sm2 = self.nv2.sample(ph * self.nv2.D * 2 + 5, self.sx * 2.1 + 40, self.sy * 2.1 + ph * 128 * 3)
        dens = np.clip(0.45 + 0.55 * (0.7 * sm + 0.3 * sm2), 0, 1.4) ** 1.6
        smoke = dens * (self.smask * 0.85 + self.smask2 * 1.2)
        litsmoke = np.array([0.030, 0.012, 0.0045], np.float32) * fl
        img = img * (1 - 0.35 * smoke[..., None]) + smoke[..., None] * litsmoke
        img *= self.vig
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)
        # altar
        ax, ay = self.abox
        A = self.altar
        coal_n = self.nv2.sample(ph * self.nv2.D * 3, A.X * 0.03, A.Y * 0.03 + ph * 128)
        arad = A.render(fl, coal_n)
        ah, aw = arad.shape[:2]
        reg = img[ay:ay + ah, ax:ax + aw]
        reg *= (1 - A.alpha); reg += arad * A.alpha
        # fire (half res -> full)
        n = fire_noise(self.nv, self.FX, self.FY, t, T, feat=85, stretch=2.9, warp=0.55, octaves=4, seed=0.0)
        I = flame(n, self.fu, self.fv, self.fprof, erosion=0.95, side_soft=0.22, gain=1.25, side_noise=0.30)
        n2 = fire_noise(self.nv, self.FX, self.FY, t, T, feat=60, stretch=2.2, warp=0.4, octaves=3, seed=3.3)
        Ic = flame(n2, self.fu * 1.05, self.fv, self.core_prof, erosion=0.5, side_soft=0.25, gain=1.5)
        fire = apply_lut(np.clip((I * 0.84 + Ic * 0.14) * self.ftop, 0, 1)) * 0.40
        FX0, FY0, FX1, FY1 = self.fbox
        fx0, fy0 = int(round(FX0 * s)), int(round(FY0 * s))
        fw, fh = int(round((FX1 - FX0) * s)), int(round((FY1 - FY0) * s))
        fire = cv2.resize(fire, (fw, fh), interpolation=cv2.INTER_CUBIC)
        # occlusion by the front of the altar
        occ = np.zeros((fh, fw, 1), np.float32)
        oy0 = ay - fy0; ox0 = ax - fx0
        fm = A.front_mask[..., None]
        ys0, ys1 = max(0, oy0), min(fh, oy0 + ah); xs0, xs1 = max(0, ox0), min(fw, ox0 + aw)
        occ[ys0:ys1, xs0:xs1] = fm[ys0 - oy0:ys1 - oy0, xs0 - ox0:xs1 - ox0]
        img[fy0:fy0 + fh, fx0:fx0 + fw] += fire * (1 - occ)
        # embers (full res)
        a1, h1 = self.emb_s.splat(t, w, h, s)
        a2, h2 = self.emb_m.splat(t, w, h, s)
        a3, h3 = self.emb_w.splat(t, w, h, s)
        sg = max(0.5, 1.0 * s)
        e = ember_rgb(blur(a1, sg), blur(h1, sg)) * 2.6 + ember_rgb(blur(a2, 3.0 * s), blur(h2, 3.0 * s)) * 1.3 + ember_rgb(blur(a3, 1.6 * s), blur(h3, 1.6 * s)) * 1.2
        img += e * (1.0 if s >= 0.5 else (0.5 / s) ** 2 * 0.25 * 4)
        img += bloom(img, s, sigmas=(8, 30, 90, 260), weights=(0.14, 0.11, 0.09, 0.07))
        disp = self.tone(img)
        # typography
        for tb in self.text_boxes:
            R = disp[tb['sl']]
            R *= (1 - 0.75 * tb['shadow'])
            screen_add(R, tb['glow'] * fl)
            over(R, tb['verse'], tb['va'])
            over(R, np.clip(tb['cA'] + fl * tb['cB'], 0, 1), tb['ta'])
        return finish(disp, self.rng, grain_amt, self.grain_size if s >= 0.5 else 0.6)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--scale', type=float, default=0.25)
    ap.add_argument('--still', default=None); ap.add_argument('--t', type=float, default=3.0)
    ap.add_argument('--video', default=None); ap.add_argument('--frames', type=int, default=int(T * FPS))
    ap.add_argument('--crf', type=int, default=17)
    ap.add_argument('--grain', type=float, default=0.026)
    ap.add_argument('--start', type=int, default=0); ap.add_argument('--end', type=int, default=-1)
    ap.add_argument('--gsize', type=float, default=1.2)
    a = ap.parse_args()
    t0 = time.time(); r = V2(a.scale); r.grain_size = a.gsize; print('init', round(time.time() - t0, 2), 's', flush=True)
    if a.still:
        t0 = time.time(); fr = r.frame(a.t, grain_amt=a.grain); print('frame', round(time.time() - t0, 2), 's')
        Image.fromarray(fr).save(a.still)
    if a.video:
        wr = FFWriter(a.video, r.w, r.h, FPS, crf=a.crf)
        t0 = time.time()
        end = a.frames if a.end < 0 else a.end
        for i in range(a.start, end):
            wr.write(r.frame(i / FPS, grain_amt=a.grain))
            if i % 30 == 0:
                print(f'{i}/{end} {time.time() - t0:.1f}s', flush=True)
        wr.close(); print('video done', round(time.time() - t0, 1))
