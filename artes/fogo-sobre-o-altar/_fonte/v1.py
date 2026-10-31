"""V1 — referência à ID 'Culto RGNR em Concerto': didone creme, grão de filme, fogo desfocado."""
import sys, os, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from fx import *
from fire import fire_noise, flame

T = 10.0
FPS = 30
LAYERS = os.environ.get('LAYERS', '/tmp/work/layers')


def bbox(a, pad=0):
    ys, xs = np.nonzero(a > 0.004)
    return max(0, xs.min() - pad), max(0, ys.min() - pad), xs.max() + 1 + pad, ys.max() + 1 + pad


class V1:
    def __init__(self, s):
        self.s = s
        w, h = int(round(W * s)), int(round(H * s)); self.w, self.h = w, h
        # background works at half the output scale (it is soft)
        self.bs = bs = s * 0.5
        bw, bh = int(round(W * bs)), int(round(H * bs)); self.bw, self.bh = bw, bh
        yy, xx = np.mgrid[0:bh, 0:bw].astype(np.float32)
        X = (xx + 0.5) / bs; Y = (yy + 0.5) / bs
        self.X, self.Y = X, Y
        self.nv = NoiseVol(N=256, D=32, kc=14, ktc=2.5, seed=11)
        self.nv2 = NoiseVol(N=128, D=16, kc=5, ktc=1.5, seed=12)
        # ---- static background (linear light)
        bg = np.zeros((bh, bw, 3), np.float32) + np.array([0.0030, 0.0026, 0.0026], np.float32)
        bg += np.exp(-((X - 700) / 1500) ** 2 - ((Y - 380) / 650) ** 2)[..., None] * np.array([0.0010, 0.0105, 0.0115], np.float32)
        bg += np.exp(-((X - 4500) / 900) ** 2 - ((Y - 200) / 500) ** 2)[..., None] * np.array([0.0006, 0.0050, 0.0060], np.float32)
        bg += np.exp(-((X - 2400) / 1900) ** 2 - ((Y - 1500) / 520) ** 2)[..., None] * np.array([0.060, 0.018, 0.0045], np.float32)
        self.bg = bg
        ang = -0.42
        dx = X - 4150; dy = Y - 380
        a1 = dx * np.cos(ang) - dy * np.sin(ang); b1 = dx * np.sin(ang) + dy * np.cos(ang)
        self.leak1 = ((np.exp(-(a1 / 1000) ** 2 - (b1 / 110) ** 2) * 0.035 + np.exp(-((X - 4850) / 650) ** 2 - ((Y - 560) / 560) ** 2) * 0.075)[..., None] * np.array([1.0, 0.36, 0.08], np.float32))
        self.leak2 = (np.exp(-((X + 80) / 520) ** 2 - ((Y - 1180) / 420) ** 2) * 0.07)[..., None] * np.array([1.0, 0.42, 0.12], np.float32)
        self.hazemask = (smoothstep(250, 1350, Y))[..., None] * np.array([0.020, 0.0085, 0.0035], np.float32)
        self.hx = (X * 0.018 + 10).astype(np.float32); self.hy = (Y * 0.026).astype(np.float32)
        self.vig = vignette(bh, bw, strength=0.42, power=2.0)[..., None]
        # fire grid (low res, defocused anyway)
        self.fs = min(bs, 1 / 5)
        fw, fh = int(W * self.fs), int(550 * self.fs)
        fx_ = (np.arange(fw, dtype=np.float32) + 0.5) / self.fs
        fy_ = 800 + (np.arange(fh, dtype=np.float32) + 0.5) / self.fs
        self.FX, self.FY = np.meshgrid(fx_, fy_)
        u = (self.FX - 2400) / 1850
        self.fu = u
        rr0 = np.random.default_rng(77)
        bumps = np.zeros_like(self.FX)
        for k in range(7):
            cx0 = 2400 + (rr0.random() - 0.5) * 3000; wd = 180 + 260 * rr0.random(); am = 0.25 + 0.45 * rr0.random()
            bumps += am * np.exp(-((self.FX - cx0) / wd) ** 2)
        self.fprof = (0.42 + 0.58 * np.cos(np.clip(u, -1.2, 1.2) * np.pi / 2.4) ** 2) * (0.8 + 0.55 * bumps)
        self.fv = (1420 - self.FY) / 330.0
        self.ffade = smoothstep(800, 900, self.FY) * (1 - 0.30 * smoothstep(1180, 1350, self.FY))
        # particles
        def spawn_bed(R, spread=1700, y0=1330, yspread=160):
            x = 2400 + (R[:, 0] - 0.5) * 2 * spread * (0.35 + 0.65 * np.abs(R[:, 0] - 0.5) * 2)
            return x, y0 + R[:, 5] * yspread
        self.emb_s = Embers(170, T, 1, lambda R: spawn_bed(R), life_m=(1, 2), speed=(110, 260), drift=55, streak=0.05, bright=(0.8, 2.6))
        self.emb_m = Embers(45, T, 2, lambda R: spawn_bed(R, 2000), life_m=(1,), speed=(70, 150), drift=80, streak=0.04, bright=(0.5, 1.4))
        def spawn_bokeh(R):
            return R[:, 0] * W, 900 + R[:, 5] * 650
        self.bok = Embers(46, T, 3, spawn_bokeh, life_m=(1,), speed=(25, 70), drift=70, streak=0.0, bright=(0.25, 0.9))
        rr = np.random.default_rng(5)
        self.bok_r = (18 + 64 * rr.random(46) ** 2.4).astype(np.float32)
        self.bok_hue = rr.random(46).astype(np.float32)
        self.tone = ToneLUT(exposure=1.25)
        # ---- typography (full res, display space), restricted to a bbox
        Lr = lambda n: load_rgba(f'{LAYERS}/v1_{n}.png', w, h)
        title, ta = Lr('title'); gold, ga = Lr('gold'); tiny, tya = Lr('tiny'); lab, la = Lr('labels')
        allA = np.maximum.reduce([ta, ga, tya, la])[..., 0]
        x0, y0, x1, y1 = bbox(allA, pad=int(90 * s))
        self.tb = (x0, y0, x1, y1)
        sl = (slice(y0, y1), slice(x0, x1))
        self.ta, self.ga, self.tya, self.la = ta[sl], ga[sl], tya[sl], la[sl]
        self.tiny, self.lab, self.gold = tiny[sl], lab[sl], gold[sl]
        ty, tx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        TX = (tx + 0.5) / s; TY = (ty + 0.5) / s
        wk = (smoothstep(560, 1000, TY) * 0.22)[..., None]
        warm = np.array([1.0, 0.80, 0.58], np.float32)
        self.tA = title[sl]                           # tcol = tA + fl*tB
        self.tB = wk * (warm - title[sl])
        self.q = (TX + 0.45 * (TY - 675)).astype(np.float32)
        self.tglow = (blur(ta[..., 0], 34 * s)[sl])[..., None] * np.array([0.10, 0.065, 0.035], np.float32)
        self.gglow = (blur(ga[..., 0], 22 * s)[sl])[..., None] * np.array([0.9, 0.55, 0.12], np.float32) * 0.55
        self.rng = np.random.default_rng(1234)
        self.grain_size = 1.2

    def flicker(self, t):
        p = TAU * t / T
        return 1 + 0.07 * np.sin(3 * p + 0.4) + 0.05 * np.sin(7 * p + 1.9) + 0.035 * np.sin(13 * p + 4.1) + 0.02 * np.sin(23 * p + 2.2)

    def background(self, t):
        bs, bw, bh = self.bs, self.bw, self.bh
        fl = self.flicker(t); p = TAU * t / T
        img = self.bg.copy()
        n = fire_noise(self.nv, self.FX, self.FY, t, T, feat=150, stretch=2.4, warp=0.55, octaves=3, seed=0.0)
        I = flame(n, self.fu, self.fv, self.fprof, erosion=0.6, side_soft=0.30, gain=1.35) * self.ffade
        fire = apply_lut(I * 0.86) * 0.21
        fire = blur(fire, 20 * self.fs)
        fire = cv2.resize(fire, (bw, int(round(550 * bs))), interpolation=cv2.INTER_CUBIC)
        y0 = int(round(800 * bs))
        img[y0:y0 + fire.shape[0]] += fire[:bh - y0]
        hz = self.nv2.sample(t / T * self.nv2.D, self.hx, self.hy + (t / T) * 128)
        img += np.clip(0.5 + 0.35 * hz, 0, 1)[..., None] * self.hazemask * fl
        img += self.leak1 * (0.75 + 0.25 * np.sin(p + 0.5))
        img += self.leak2 * (0.8 + 0.2 * np.sin(p * 2 + 2.0))
        # bokeh
        bx, by, _, _, bb, heat, R = self.bok.state(t)
        bok = np.zeros((bh, bw), np.float32); bokh = np.zeros((bh, bw), np.float32)
        for i in range(len(bx)):
            if bb[i] < 0.01:
                continue
            r = max(1, int(self.bok_r[i] * bs)); cx, cy = int(bx[i] * bs), int(by[i] * bs)
            cv2.circle(bok, (cx, cy), r, float(bb[i]), -1, lineType=cv2.LINE_8)
            cv2.circle(bokh, (cx, cy), r, float(bb[i] * self.bok_hue[i]), -1, lineType=cv2.LINE_8)
        bok = blur(bok, 6.6 * bs); bokh = blur(bokh, 6.6 * bs)
        img += ember_rgb(bok * 0.22, bokh * 0.22, cold=(1.0, 0.30, 0.06), hot=(1.2, 0.62, 0.22))
        # embers
        a, ha = self.emb_s.splat(t, bw, bh, bs)
        sg = max(0.5, 1.1 * bs * 2)
        a = blur(a, sg); ha = blur(ha, sg)
        am, ham = self.emb_m.splat(t, bw, bh, bs)
        am = blur(am, 4.0 * bs); ham = blur(ham, 4.0 * bs)
        k = (0.5 / bs) ** 2 * 0.25   # keep energy independent of resolution (splat area)
        img += (ember_rgb(a, ha) * 2.2 + ember_rgb(am, ham) * 0.9) * min(1.0, 4 * k) * (1 if bs >= 0.25 else 4 * bs)
        img *= (0.92 + 0.08 * fl)
        img += bloom(img, bs, sigmas=(10, 40, 140), weights=(0.18, 0.15, 0.16))
        disp = self.tone(img)
        lum = disp.mean(-1, keepdims=True)
        disp += (1 - lum) ** 4 * np.array([-0.004, 0.010, 0.012], np.float32)
        disp *= self.vig
        return disp, fl

    def frame(self, t, grain_amt=0.032):
        s, w, h = self.s, self.w, self.h
        dbg, fl = self.background(t)
        disp = cv2.resize(dbg, (w, h), interpolation=cv2.INTER_CUBIC)
        x0, y0, x1, y1 = self.tb
        R = disp[y0:y1, x0:x1]
        over(R, self.tiny, self.tya)
        tp = (t % T) / T
        sweep_c = -900 + (4800 + 1800) * smoothstep(0.08, 0.62, tp)
        band = np.exp(-((self.q - sweep_c) / 210) ** 2)[..., None]
        tcol = self.tA + fl * self.tB + band * 0.22
        screen_add(R, self.tglow * (0.8 + 0.4 * band))
        over(R, np.clip(tcol, 0, 1), self.ta)
        screen_add(R, self.gglow * (0.55 + 0.45 * fl))
        over(R, np.clip(self.gold * (0.92 + 0.36 * (fl - 1)), 0, 1), self.ga)
        over(R, self.lab, self.la)
        return finish(disp, self.rng, grain_amt, self.grain_size if s >= 0.5 else 0.6)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--scale', type=float, default=0.25)
    ap.add_argument('--still', default=None); ap.add_argument('--t', type=float, default=3.0)
    ap.add_argument('--video', default=None); ap.add_argument('--frames', type=int, default=int(T * FPS))
    ap.add_argument('--crf', type=int, default=17)
    ap.add_argument('--grain', type=float, default=0.032)
    ap.add_argument('--start', type=int, default=0); ap.add_argument('--end', type=int, default=-1)
    ap.add_argument('--gsize', type=float, default=1.2)
    a = ap.parse_args()
    t0 = time.time(); r = V1(a.scale); r.grain_size = a.gsize; print('init', round(time.time() - t0, 2), 's', flush=True)
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
