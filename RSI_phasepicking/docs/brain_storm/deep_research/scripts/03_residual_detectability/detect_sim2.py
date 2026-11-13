"""Monte Carlo: can leave-one-out (jackknife) residuals find a single wrong pick?
Homogeneous half-space, single-event location by Gauss-Newton; deleted residual
d_i = r_i/(1-h_ii) (linearised leave-one-out), studentised by a robust scale (MAD)
of the other picks. Pick noise Laplace(20 ms P, 40 ms S) after Yu et al. 2025;
model error = per-station Gaussian term sigma_m (P), x1.73 for S."""
import numpy as np, sys
rng = np.random.default_rng(1)
VP, VS = 6.0, 6.0/1.73
def simulate(nsta, pS, sig_m, delta, n_ev=300, thr=3.0, depth=8.0):
    out = dict(det=0, flag_any=0, zmax=[], hit=[], h_inj=[], dh=[], dz=[], dh0=[], dz0=[], npk=[])
    for _ in range(n_ev):
        r = 50*np.sqrt(rng.random(nsta)); a = 2*np.pi*rng.random(nsta)
        sx, sy = r*np.cos(a), r*np.sin(a)
        rows = []  # (sta, phase)
        for k in range(nsta):
            rows.append((k, 0))
            if rng.random() < pS: rows.append((k, 1))
        rows = np.array(rows); n = len(rows)
        if n < 6: continue
        v = np.where(rows[:,1]==0, VP, VS); scale = np.where(rows[:,1]==0, 1.0, 1.73)
        true = np.array([0.0, 0.0, depth, 0.0])
        def tt(m):
            dx = sx[rows[:,0]]-m[0]; dy = sy[rows[:,0]]-m[1]; dz = -m[2]
            R = np.sqrt(dx**2+dy**2+dz**2)
            return m[3] + R/v, dx, dy, dz, R
        t_true = tt(true)[0]
        noise = rng.laplace(0, np.where(rows[:,1]==0, 0.02, 0.04))
        stn = rng.normal(0, sig_m, (nsta,)); model = stn[rows[:,0]]*scale
        obs0 = t_true + noise + model
        inj = rng.integers(n); obs = obs0.copy()
        obs[inj] += delta*rng.choice([-1,1])
        def locate(o):
            m = np.array([rng.normal(0,2), rng.normal(0,2), 6.0, 0.0])
            for it in range(15):
                t, dx, dy, dz, R = tt(m)
                J = np.column_stack([-dx/(R*v), -dy/(R*v), -dz/(R*v), np.ones(n)]) / scale[:,None]
                res = (o - t)/scale
                step, *_ = np.linalg.lstsq(J, res, rcond=None)
                m = m + step; m[2] = np.clip(m[2], 0.1, 40)
                if np.linalg.norm(step[:3]) < 1e-4: break
            t, dx, dy, dz, R = tt(m)
            J = np.column_stack([-dx/(R*v), -dy/(R*v), -dz/(R*v), np.ones(n)]) / scale[:,None]
            res = (o - t)/scale
            H = J @ np.linalg.pinv(J.T@J) @ J.T
            return m, res, np.clip(np.diag(H), 0, 0.999)
        m0, _, _ = locate(obs0)
        m, res, h = locate(obs)
        d = res/(1-h)                       # deleted residual
        z = np.empty(n)
        for i in range(n):                  # robust scale of the others
            oth = np.delete(res/np.sqrt(1-h), i)
            s = 1.4826*np.median(np.abs(oth - np.median(oth))) + 1e-4
            z[i] = (res[i]/np.sqrt(1-h[i]))/s
        i_max = np.argmax(np.abs(z))
        out['zmax'].append(np.abs(z[i_max])); out['hit'].append(i_max == inj)
        out['h_inj'].append(h[inj]); out['npk'].append(n)
        out['dh'].append(np.hypot(m[0]-m0[0], m[1]-m0[1])); out['dz'].append(abs(m[2]-m0[2]))
        out['dh0'].append(np.hypot(m0[0], m0[1])); out['dz0'].append(abs(m0[2]-depth))
    N = len(out['dh'])
    return dict(N=N, zmax=np.array(out['zmax']), hit=np.array(out['hit']), h=np.median(out['h_inj']),
                npk=np.median(out['npk']), dh=np.median(out['dh']), dz=np.median(out['dz']),
                dh90=np.percentile(out['dh'],90), dz90=np.percentile(out['dz'],90),
                base_dh=np.median(out['dh0']), base_dz=np.median(out['dz0']))

print("net nsta sig_m delta | npk h_inj | thr95 | detect@5%FA | shift_h med/p90 km  shift_z med/p90 km | base err h/z (no pick error)")
for name, nsta, pS in [("dense",20,0.6),("sparse",7,0.5)]:
    for sig_m in [0.0, 0.05, 0.10, 0.15]:
        r0 = simulate(nsta, pS, sig_m, 0.0, n_ev=600)
        thr = np.percentile(r0['zmax'], 95)
        for delta in [0.05, 0.1, 0.3, 1.0]:
            r = simulate(nsta, pS, sig_m, delta, n_ev=400)
            det = np.mean((r['zmax'] > thr) & r['hit'])
            print(f"{name} {nsta} {sig_m:.2f} {delta:.2f} | {r['npk']:.0f} {r['h']:.2f} | {thr:.1f} | {det:.2f} | {r['dh']:.3f}/{r['dh90']:.3f} {r['dz']:.3f}/{r['dz90']:.3f} | {r0['base_dh']:.2f}/{r0['base_dz']:.2f}", flush=True)
