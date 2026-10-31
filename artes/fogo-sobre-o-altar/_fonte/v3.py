"""V3 — Tipográfica incandescente: letras preenchidas de fogo vivo, chamas saindo do topo, brasas."""
import sys, os, argparse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image
from fx import *
from fire import fire_noise, flame

T = 10.0
FPS = 30
LAYERS = os.environ.get('LAYERS', '/tmp/work/layers')
LUT_FILL = make_lut([
    (0.00, (0.00, 0.00, 0.00)),
    (0.20, (0.25, 0.02, 0.00)),
    (0.38, (0.95, 0.12, 0.01)),
    (0.55, (1.70, 0.42, 0.04)),
    (0.70, (2.40, 0.95, 0.14)),
    (0.85, (3.00, 1.70, 0.50)),
    (1.00, (3.60, 2.80, 1.50)),
])


class V3:
    def __init__(self, s):
        self.s = s
        w, h = int(round(W * s)), int(round(H * s)); self.w, self.h = w, h
        self.nv = NoiseVol(N=256, D=32, kc=14, ktc=2.5, seed=51)
        self.nv2 = NoiseVol(N=128, D=16, kc=6, ktc=1.5, seed=52)
        ta_rgb, ta = load_rgba(f'{LAYERS}/v3_title.png', w, h); self.ta = ta
        self.ref, self.refa = load_rgba(f'{LAYERS}/v3_ref.png', w, h)
        # letter bbox (full-res units)
        TX0, TY0, TX1, TY1 = 300, 560, 4500, 1080
        self.tbox = (TX0, TY0, TX1, TY1)
        # fill grid at half res
        self.fs = fs = s * 0.5
        self.LX, self.LY = grid(TX0, TY0, TX1, TY1, fs)
        x0, y0 = int(round(TX0 * s)), int(round(TY0 * s)); x1, y1 = x0 + int(round((TX1 - TX0) * s)), y0 + int(round((TY1 - TY0) * s))
        self.tsl = (slice(y0, y1), slice(x0, x1))
        A = ta[self.tsl][..., 0]
        e = blur(A, 7 * s)
        self.edge = (0.80 + 0.20 * np.clip((e - 0.5) * 2.2, 0, 1)).astype(np.float32)
        self.vgrad = smoothstep(1043, 606, (np.mgrid[y0:y1, 0:1][0].astype(np.float32) + 0.5) / s)
        # letter tops per column (full output res)
        full_a = ta[..., 0] > 0.5
        has = full_a.any(0)
        top = np.where(has, full_a.argmax(0), 10 ** 6).astype(np.float32) / s   # full-res units
        from scipy.ndimage import maximum_filter1d
        top = maximum_filter1d(top, size=2 * max(1, int(round(7 * s))) + 1)
        top = np.where(top < 650, top, 10 ** 6).astype(np.float32)   # only near the cap line
        self.top_full = top
        # flame grid at half res
        FX0, FY0, FX1, FY1 = 300, 60, 4500, 1060
        self.fbox = (FX0, FY0, FX1, FY1)
        self.FX, self.FY = grid(FX0, FY0, FX1, FY1, fs)
        colx = np.clip((self.FX[0] * s).astype(np.int64), 0, w - 1)
        topc = top[colx]
        # smooth the top profile a little (only where letters exist)
        valid = topc < 10 ** 5
        tp = np.where(valid, topc, 1300.0).astype(np.float32)
        tp_s = cv2.GaussianBlur(tp[None, :], (0, 0), sigmaX=max(1.0, 10 * fs))[0]
        tp = np.where(valid, np.minimum(tp, tp_s + 12), 10 ** 6)
        self.d = (tp[None, :] - self.FY).astype(np.float32)    # distance above letter top
        r0 = np.random.default_rng(9)
        bumps = np.ones_like(self.FX[0])
        bumps *= 0.55
        for k in range(14):
            c0 = 400 + r0.random() * 4000; wd = 50 + 140 * r0.random(); am = 0.3 + 0.9 * r0.random()
            bumps += am * np.exp(-((self.FX[0] - c0) / wd) ** 2)
        self.fprof = np.broadcast_to(bumps[None, :], self.FX.shape).astype(np.float32)
        self.zero = np.zeros_like(self.FX)
        # smoke grid (quarter)
        self.ss = s * 0.25
        self.SX, self.SY = grid(0, 0, W, H, self.ss)
        colx2 = np.clip((self.SX[0] * s).astype(np.int64), 0, w - 1)
        tps = top[colx2]
        tps = np.where(tps < 10 ** 5, tps, 2000.0)
        tps = cv2.GaussianBlur(tps.astype(np.float32)[None, :], (0, 0), sigmaX=max(1.0, 60 * self.ss))[0]
        ds = tps[None, :] - self.SY
        self.smask = (smoothstep(60, 260, ds) * (1 - smoothstep(380, 820, ds))).astype(np.float32)
        # background (quarter) : deep red glow behind the title
        X, Y = self.SX, self.SY
        bg = np.zeros(X.shape + (3,), np.float32) + np.array([0.0018, 0.0012, 0.0012], np.float32)
        env = smoothstep(0, 700, X) * smoothstep(W, W - 700, X)
        bg += (np.exp(-((Y - 800) / 420) ** 2) * env)[..., None] * np.array([0.030, 0.0045, 0.0008], np.float32)
        bg += (np.exp(-((Y - 1350) / 260) ** 2) * env)[..., None] * np.array([0.012, 0.0025, 0.0006], np.float32)
        self.bg = bg
        self.vig = vignette(X.shape[0], X.shape[1], strength=0.55, power=2.0)[..., None]
        # embers spawn from letter tops
        cols = np.nonzero(top < 10 ** 5)[0]
        self.cols_x = (cols.astype(np.float32) + 0.5) / s
        self.cols_top = top[cols]
        def spawn(R):
            i = (R[:, 0] * (len(self.cols_x) - 1)).astype(np.int64)
            return self.cols_x[i], self.cols_top[i] - R[:, 5] * 120
        self.emb_s = Embers(420, T, 61, spawn, life_m=(1, 2, 3), speed=(120, 330), drift=70, streak=0.06, bright=(0.8, 3.0))
        self.emb_m = Embers(80, T, 62, spawn, life_m=(1, 2), speed=(80, 200), drift=120, streak=0.05, bright=(0.5, 1.6))
        self.tone = ToneLUT(exposure=1.1)
        self.rng = np.random.default_rng(7)
        self.grain_size = 1.2

    def flicker(self, t):
        p = TAU * t / T
        return 1 + 0.06 * np.sin(5 * p + 0.4) + 0.045 * np.sin(11 * p + 1.9) + 0.03 * np.sin(19 * p + 4.1)

    def frame(self, t, grain_amt=0.022):
        s, w, h = self.s, self.w, self.h
        fl = self.flicker(t); ph = t / T
        # --- background + smoke at quarter res
        sm = self.nv2.sample(ph * self.nv2.D, self.SX * 0.022, self.SY * 0.018 + ph * 128 * 2)
        sm2 = self.nv2.sample(ph * self.nv2.D * 2 + 3, self.SX * 0.05 + 50, self.SY * 0.04 + ph * 128 * 4)
        dens = np.clip(0.5 + 0.5 * (0.7 * sm + 0.3 * sm2), 0, 1.3) ** 1.8 * self.smask
        img = self.bg * (0.9 + 0.1 * fl) + dens[..., None] * np.array([0.020, 0.0075, 0.003], np.float32)
        img *= self.vig
        img = cv2.resize(img, (w, h), interpolation=cv2.INTER_LINEAR)
        # --- flames above the letters (half res)
        n = fire_noise(self.nv, self.FX, self.FY, t, T, feat=62, stretch=2.6, warp=0.6, octaves=4, seed=1.0)
        v = self.d / 135.0
        I = flame(n, self.zero, v, self.fprof, erosion=1.15, side_soft=0.3, gain=1.15, side_noise=0.0)
        I = I * smoothstep(2, 16, self.d) * smoothstep(60, 300, self.FY)
        fire = apply_lut(I * 0.78) * 0.32
        FX0, FY0, FX1, FY1 = self.fbox
        fx0, fy0 = int(round(FX0 * s)), int(round(FY0 * s))
        fw, fh = int(round((FX1 - FX0) * s)), int(round((FY1 - FY0) * s))
        img[fy0:fy0 + fh, fx0:fx0 + fw] += cv2.resize(fire, (fw, fh), interpolation=cv2.INTER_CUBIC)
        # --- molten fill (half res -> full), masked by letters
        nf = fire_noise(self.nv, self.LX, self.LY, t, T, feat=55, stretch=3.2, warp=0.35, octaves=4, seed=7.0, speed=1)
        If = np.clip(0.84 + 0.26 * nf, 0, 1)
        fill = apply_lut(If, LUT_FILL)
        sl = self.tsl
        fh2, fw2 = sl[0].stop - sl[0].start, sl[1].stop - sl[1].start
        fill = cv2.resize(fill, (fw2, fh2), interpolation=cv2.INTER_CUBIC)
        fill *= (self.edge * (0.86 + 0.14 * self.vgrad[:, :1]))[..., None] * (0.42 * (0.94 + 0.06 * fl))
        A = self.ta[sl]
        R = img[sl]
        R *= (1 - A)
        R += fill * A
        # --- floor reflection of the letters
        refl_src = (fill * A)[::-1]
        rh = min(fh2, h - (sl[0].stop))
        if rh > 0:
            fade = np.exp(-np.arange(rh, dtype=np.float32) / (90 * s))[:, None, None] * 0.045
            img[sl[0].stop:sl[0].stop + rh, sl[1]] += blur(refl_src[:rh], 5 * s) * fade
        # --- embers
        a1, h1 = self.emb_s.splat(t, w, h, s); a2, h2 = self.emb_m.splat(t, w, h, s)
        sg = max(0.5, 1.0 * s)
        img += ember_rgb(blur(a1, sg), blur(h1, sg)) * 2.6 + ember_rgb(blur(a2, 3.0 * s), blur(h2, 3.0 * s)) * 1.2
        img += bloom(img, s, sigmas=(8, 28, 90, 240), weights=(0.12, 0.10, 0.08, 0.07))
        disp = self.tone(img)
        over(disp, self.ref, self.refa * 0.75)
        return finish(disp, self.rng, grain_amt, self.grain_size if s >= 0.5 else 0.6)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--scale', type=float, default=0.25)
    ap.add_argument('--still', default=None); ap.add_argument('--t', type=float, default=3.0)
    ap.add_argument('--video', default=None); ap.add_argument('--frames', type=int, default=int(T * FPS))
    ap.add_argument('--crf', type=int, default=19)
    ap.add_argument('--grain', type=float, default=0.022)
    ap.add_argument('--gsize', type=float, default=1.2)
    ap.add_argument('--start', type=int, default=0); ap.add_argument('--end', type=int, default=-1)
    a = ap.parse_args()
    t0 = time.time(); r = V3(a.scale); r.grain_size = a.gsize; print('init', round(time.time() - t0, 2), 's', flush=True)
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
