"""Report existing confirmation geometry; no fitting or event reselection."""
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.colors import Normalize

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'export/51_confirmation'


def main():
    before = pd.read_csv(OUT / 'inputs/events.csv').query("role == 'reserve'").set_index('event_id')
    after = pd.read_csv(OUT / 'events.csv').query("role == 'reserve' and branch == 'joint_all'").set_index('event_id')
    assert before.index.is_unique and after.index.is_unique
    assert len(before) == len(after) == 300 and set(before.index) == set(after.index)
    after = after.loc[before.index]
    flagged = (after.depth_km < .5) | (after.depth_km > 24.5)
    assert flagged.sum() == 6
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 10,
                         'axes.spines.top': False, 'axes.spines.right': False,
                         'pdf.fonttype': 42})
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), layout='constrained')
    extent = {}
    for key in ['x_km', 'y_km']:
        vals = np.r_[before[key], after[key]]
        extent[key] = (vals.min() - 2, vals.max() + 2)
    norm = Normalize(0, 25)
    for row, (frame, name) in enumerate([(before, 'Original NLL'), (after, 'Joint candidate')]):
        for col, (x, y) in enumerate([('x_km', 'y_km'), ('x_km', 'depth_km'), ('y_km', 'depth_km')]):
            ax = axes[row, col]
            points = ax.scatter(frame[x], frame[y], c=frame.depth_km, cmap='viridis_r',
                                norm=norm, s=12, alpha=.85, linewidths=0, rasterized=True)
            ax.scatter(frame.loc[flagged, x], frame.loc[flagged, y], s=48,
                       facecolors='none', edgecolors='#D55E00', linewidths=1,
                       label='Six joint depth flags')
            ax.set_xlim(extent[x])
            ax.set_xlabel('East (km)' if x == 'x_km' else 'North (km)')
            ax.set_ylabel('North (km)' if col == 0 else 'Model depth (km)')
            if col == 0:
                ax.set_ylim(extent[y])
                ax.set_aspect('equal', adjustable='box')
            else:
                ax.set_ylim(25.5, -.5)
            ax.set_title(f'{"abcdef"[row * 3 + col]}  {name}', loc='left', fontsize=11)
    axes[0, 0].legend(frameon=False, fontsize=8, loc='upper right')
    fig.colorbar(points, ax=axes, label='Model depth (km)', shrink=.75, pad=.02)
    dest = OUT / 'figures'
    dest.mkdir(exist_ok=True)
    for suffix in ['png', 'pdf']:
        fig.savefig(dest / f'catalog_geometry_comparison.{suffix}', dpi=220)
    plt.close(fig)
    print('Saved', dest / 'catalog_geometry_comparison.png')


if __name__ == '__main__':
    main()
