"""Shared FX toolkit: periodic noise, fire ramp, embers, bloom, grading, ffmpeg IO.
Everything that moves is periodic in T, so every video loops seamlessly."""
import numpy as np, cv2, subprocess, os, json
from PIL import Image

if os.environ.get('CV_THREADS'):
    cv2.setNumThreads(int(os.environ['CV_THREADS']))

W, H = 4800, 1350
TAU = 2 * np.pi


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class NoiseVol:
    """Band-limited noise, periodic in (time, y, x). Zero mean, unit std."""
    def __init__(self, N=256, D=32, kc=14.0, ktc=2.5, seed=0):
        rng = np.random.default_rng(seed)
        white = rng.standard_normal((D, N, N)).astype(np.float32)
        F = np.fft.fftn(white)
        kt = np.fft.fftfreq(D) * D
        k = np.fft.fftfreq(N) * N
        KT, KY, KX = np.meshgrid(kt, k, k, indexing='ij')
        K = np.sqrt(KX ** 2 + KY ** 2)
        filt = np.exp(-(K / kc) ** 2) * np.exp(-(KT / ktc) ** 2)
        filt[:, 0, 0] = 0
        v = np.real(np.fft.ifftn(F * filt)).astype(np.float32)
        v /= v.std()
        self.v, self.N, self.D = v, N, D

    def slice(self, tau):
        tau = tau % self.D
        i0 = int(np.floor(tau)); f = np.float32(tau - i0)
        return (1 - f) * self.v[i0] + f * self.v[(i0 + 1) % self.D]

    def sample(self, tau, mx, my):
        N = self.N
        s = self.slice(tau)
        return cv2.remap(s, np.mod(mx, N).astype(np.float32), np.mod(my, N).astype(np.float32),
                         cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)


def grid(x0, y0, x1, y1, scale):
    """Pixel-centre coordinates (in FULL-RES units) for a region rendered at `scale`."""
    w = max(1, int(round((x1 - x0) * scale))); h = max(1, int(round((y1 - y0) * scale)))
    xs = (x0 + (np.arange(w, dtype=np.float32) + 0.5) / scale)
    ys = (y0 + (np.arange(h, dtype=np.float32) + 0.5) / scale)
    X, Y = np.meshgrid(xs, ys)
    return X, Y


def make_lut(stops, n=1024):
    """stops: list of (pos, (r,g,b)) linear colours -> LUT (n,3)."""
    p = np.array([s[0] for s in stops]); c = np.array([s[1] for s in stops], dtype=np.float32)
    x = np.linspace(0, 1, n)
    return np.stack([np.interp(x, p, c[:, i]) for i in range(3)], -1).astype(np.float32)


FIRE_LUT = make_lut([
    (0.00, (0.000, 0.000, 0.000)),
    (0.10, (0.060, 0.004, 0.000)),
    (0.24, (0.320, 0.030, 0.002)),
    (0.40, (0.900, 0.140, 0.010)),
    (0.56, (1.600, 0.420, 0.040)),
    (0.72, (2.300, 0.950, 0.160)),
    (0.86, (2.900, 1.700, 0.520)),
    (1.00, (3.400, 2.700, 1.500)),
])


def apply_lut(I, lut=FIRE_LUT):
    n = lut.shape[0]
    idx = np.clip(I * (n - 1), 0, n - 1).astype(np.int32)
    return lut[idx]


def blur(img, sigma):
    if sigma <= 0.3:
        return img
    return cv2.GaussianBlur(img, (0, 0), sigmaX=sigma, sigmaY=sigma, borderType=cv2.BORDER_REPLICATE)


def bloom(hdr, scale, sigmas=(6, 18, 48, 120), weights=(0.5, 0.35, 0.25, 0.18), thresh=0.0):
    """Multi-radius glow; sigmas in full-res px. Computed on a 1/4 buffer for speed."""
    h, w = hdr.shape[:2]
    src = np.maximum(hdr - thresh, 0) if thresh > 0 else hdr
    ds = 4
    small = cv2.resize(src, (max(1, w // ds), max(1, h // ds)), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(small)
    for s, wt in zip(sigmas, weights):
        acc += wt * blur(small, s * scale / ds)
    return cv2.resize(acc, (w, h), interpolation=cv2.INTER_LINEAR)


def aces(x):
    a, b, c, d, e = 2.51, 0.03, 2.43, 0.59, 0.14
    return np.clip((x * (a * x + b)) / (x * (c * x + d) + e), 0, 1)


def to_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, 12.92 * x, 1.055 * np.power(x, 1 / 2.4) - 0.055).astype(np.float32)


def from_srgb(x):
    return np.where(x <= 0.04045, x / 12.92, ((x + 0.055) / 1.055) ** 2.4).astype(np.float32)


def load_rgba(path, w, h):
    im = Image.open(path).convert('RGBA')
    if im.size != (w, h):
        im = im.resize((w, h), Image.LANCZOS)
    a = np.asarray(im).astype(np.float32) / 255.0
    return a[..., :3].copy(), a[..., 3:4].copy()


def grain(h, w, rng, amount, size=1.0):
    g = rng.standard_normal((h, w)).astype(np.float32)
    if size > 0.6:
        g = blur(g, size * 0.6)
        g /= max(g.std(), 1e-6)
    return g * amount


def vignette(h, w, strength=0.55, power=2.2, cx=0.5, cy=0.5, aspect=None):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (x / w - cx) * 2; ny = (y / h - cy) * 2
    r = np.sqrt((nx * 0.62) ** 2 + (ny * 1.0) ** 2) if aspect is None else np.sqrt((nx * aspect) ** 2 + ny ** 2)
    return (1 - strength * np.clip(r, 0, 1.6) ** power / (1.6 ** power) * 1.6).astype(np.float32)


class Embers:
    """Periodic particle system. Each particle's life = T/m (integer m), so the
    whole system repeats exactly every T seconds."""
    def __init__(self, n, T, seed, spawn, life_m=(1, 2), speed=(120, 320), drift=60,
                 wob=(0.4, 1.6), size=1.0, bright=(0.6, 1.6), color='ember', streak=0.06):
        rng = np.random.default_rng(seed)
        self.n, self.T = n, T
        self.m = rng.choice(life_m, n).astype(np.float32)
        self.phase = rng.random(n).astype(np.float32)
        self.seeds = rng.integers(0, 2**31 - 1, n)
        self.spawn = spawn            # function(rng_arr, n) -> (x0, y0)
        self.speed, self.drift, self.wob = speed, drift, wob
        self.bright, self.streak, self.size = bright, streak, size
        # per-cycle randomness table: max m cycles
        mm = int(max(life_m))
        r = np.random.default_rng(seed + 7)
        self.tab = r.random((mm, n, 8)).astype(np.float32)
        self.color = color

    def state(self, t):
        T = self.T
        L = T / self.m
        cyc_f = t / L + self.phase
        age = (cyc_f % 1.0).astype(np.float32)
        cyc = (np.floor(cyc_f).astype(np.int64) % self.m.astype(np.int64))
        R = self.tab[cyc, np.arange(self.n)]
        x0, y0 = self.spawn(R)
        sp = self.speed[0] + (self.speed[1] - self.speed[0]) * R[:, 2]
        tt = age * L
        wf = self.wob[0] + (self.wob[1] - self.wob[0]) * R[:, 3]
        dx = self.drift * (np.sin(TAU * (wf * tt / 2.0) + 6.28 * R[:, 4]) + 0.6 * np.sin(TAU * (wf * 2.3 * tt / 2.0) + 6.28 * R[:, 5]))
        side = (R[:, 6] - 0.5) * 2 * self.drift * 1.2 * tt / 2.0
        x = x0 + dx + side
        y = y0 - sp * tt * (1 - 0.18 * age)
        vx = self.drift * TAU * wf / 2.0 * np.cos(TAU * (wf * tt / 2.0) + 6.28 * R[:, 4]) + (R[:, 6] - 0.5) * 2 * self.drift * 0.6
        vy = -sp
        fade = smoothstep(0.0, 0.08, age) * (1 - smoothstep(0.55, 1.0, age))
        flick = 0.65 + 0.35 * np.sin(TAU * (3 + 5 * R[:, 7]) * tt + 6.28 * R[:, 1])
        b = (self.bright[0] + (self.bright[1] - self.bright[0]) * R[:, 1] ** 2) * fade * flick
        heat = 1 - age  # hot when young
        return x, y, vx, vy, b, heat, R

    def splat(self, t, w, h, scale, x_off=0, y_off=0, sub=6):
        """Accumulate streaks into an (h,w) intensity buffer + heat buffer."""
        x, y, vx, vy, b, heat, R = self.state(t)
        acc = np.zeros((h, w), np.float32)
        hacc = np.zeros((h, w), np.float32)
        for k in range(sub):
            f = k / max(1, sub - 1)
            px = ((x - vx * self.streak * f) - x_off) * scale
            py = ((y - vy * self.streak * f) - y_off) * scale
            ix = np.floor(px).astype(np.int64); iy = np.floor(py).astype(np.int64)
            fx = (px - ix).astype(np.float32); fy = (py - iy).astype(np.float32)
            ww = (b / sub) * (1 - 0.5 * f)
            for ddx, ddy, wgt in ((0, 0, (1 - fx) * (1 - fy)), (1, 0, fx * (1 - fy)), (0, 1, (1 - fx) * fy), (1, 1, fx * fy)):
                xx = ix + ddx; yy = iy + ddy
                ok = (xx >= 0) & (xx < w) & (yy >= 0) & (yy < h)
                np.add.at(acc, (yy[ok], xx[ok]), (ww * wgt)[ok])
                np.add.at(hacc, (yy[ok], xx[ok]), (ww * wgt * heat)[ok])
        return acc, hacc


def ember_rgb(acc, hacc, cold=(1.0, 0.18, 0.02), hot=(1.6, 0.75, 0.22)):
    h = np.clip(hacc / np.maximum(acc, 1e-6), 0, 1)[..., None]
    c0 = np.array(cold, np.float32); c1 = np.array(hot, np.float32)
    return acc[..., None] * (c0 * (1 - h) + c1 * h)


class FFWriter:
    def __init__(self, path, w, h, fps=30, crf=19, preset='slow', tune=None):
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
               '-r', str(fps), '-i', '-', '-c:v', 'libx264', '-preset', preset, '-crf', str(crf),
               '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart']
        if tune:
            cmd += ['-tune', tune]
        if os.environ.get('X264_LOWMEM'):
            cmd += ['-x264-params', 'rc-lookahead=20:threads=3']
        cmd += [path]
        self.p = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    def write(self, rgb8):
        self.p.stdin.write(np.ascontiguousarray(rgb8).tobytes())

    def close(self):
        self.p.stdin.close(); self.p.wait()


def finish(disp, rng, grain_amt=0.035, grain_size=1.2):
    """disp: display-space float image (0..1). adds grain, returns uint8."""
    h, w = disp.shape[:2]
    if grain_amt > 0:
        g = grain(h, w, rng, grain_amt, grain_size)[..., None]
        # grain stronger in mids, weaker in deep blacks / highlights
        lum = disp.mean(-1, keepdims=True)
        disp = disp + g * (0.35 + 0.65 * (4 * lum * (1 - lum)).clip(0, 1))
    return (np.clip(disp, 0, 1) * 255 + 0.5).astype(np.uint8)


class ToneLUT:
    """Fast ACES + sRGB via sqrt-spaced 1D LUT (input linear 0..xmax)."""
    def __init__(self, exposure=1.0, xmax=24.0, n=8192):
        self.xmax, self.n = xmax, n
        q = np.linspace(0, 1, n, dtype=np.float64)
        x = (q ** 2) * xmax
        self.lut = to_srgb(aces((x * exposure).astype(np.float32))).astype(np.float32)

    def __call__(self, img):
        q = np.sqrt(np.clip(img, 0, self.xmax) * (1.0 / self.xmax))
        idx = (q * (self.n - 1)).astype(np.int32)
        return self.lut[idx]


def over(dst, col, a):
    """in-place alpha over (straight colour)."""
    dst *= (1 - a)
    dst += col * a
    return dst


def screen_add(dst, g):
    dst += g * (1 - dst)
    return dst
