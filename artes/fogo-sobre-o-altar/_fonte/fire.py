import numpy as np
from fx import NoiseVol, smoothstep


def fire_noise(nv, X, Y, t, T, feat=110.0, stretch=2.6, warp=0.5, octaves=4, seed=0.0, speed=1):
    """Turbulent, upward-flowing, perfectly periodic fbm in roughly [-1,1]."""
    N, D = nv.N, nv.D
    ph = t / T
    sx = 32.0 / (2 * feat); sy = sx / stretch
    # low-frequency domain warp (1 tile scroll per loop)
    wx = nv.sample(ph * D + 7.3 + seed, X * sx * 0.33 + 40.0 + seed * 13, Y * sy * 0.33 + ph * N * speed)
    wy = nv.sample(ph * D + 19.1 + seed, X * sx * 0.33 + 140.0 + seed * 7, Y * sy * 0.33 + ph * N * speed + 60)
    Xw = X + wx * feat * warp
    Yw = Y + wy * feat * warp * 1.3
    n = 0.0; amp = 1.0; tot = 0.0
    scrolls = (1, 2, 5, 10, 20)
    tsteps = (1, 2, 3, 4, 6)
    for i in range(octaves):
        f = 2 ** i
        n = n + amp * nv.sample(ph * D * tsteps[i] + 5.1 * i + seed, Xw * sx * f + 31.7 * i + seed * 3,
                                Yw * sy * f + ph * N * scrolls[i] * speed)
        tot += amp * amp; amp *= 0.52
    return n * (0.45 / np.sqrt(tot))


def flame(n, u, v, prof, erosion=0.55, side_soft=0.35, gain=1.6, side_noise=0.18):
    """u: horizontal coord normalised to half-width (|u|<1 inside), v: 0 at base -> 1 at nominal top.
    prof: height multiplier. n: noise (std~0.45). Returns intensity in [0,1]."""
    vv = v / np.maximum(prof, 1e-3)
    e = np.maximum(n * erosion, -0.62)          # never let erosion flip sign (avoids stray blobs)
    vd = vv + e * (0.12 + vv)
    f = (1.0 - vd) * (1.0 - smoothstep(1.35, 2.0, vv))
    f = f * smoothstep(1.0 + side_soft, 1.0 - side_soft, np.abs(u) + n * side_noise)
    f = f * smoothstep(-0.04, 0.03, v)
    return np.clip(f * gain, 0, 1)
