#!/usr/bin/env python3
"""Shared layout and export choices for the Kilauea figures.

Mirrors the Ridgecrest figure conventions: 180 mm width, embedded TrueType in
PDF, PNG+PDF pairs saved by `save_figure`. Kept dependency-free so every
figure script in this directory can import it.
"""
from pathlib import Path

import matplotlib

WIDTH_INCHES = 180 / 25.4


def publication_style():
    return matplotlib.rc_context({
        'font.family': 'DejaVu Sans', 'font.size': 7.5, 'axes.titlesize': 8,
        'axes.labelsize': 7.5, 'xtick.labelsize': 6.5, 'ytick.labelsize': 6.5,
        'legend.fontsize': 6.5, 'axes.linewidth': .65,
        'lines.linewidth': 1.1, 'xtick.major.width': .6, 'ytick.major.width': .6,
        'xtick.major.size': 2.8, 'ytick.major.size': 2.8,
        'axes.spines.top': False, 'axes.spines.right': False,
        'axes.unicode_minus': True, 'pdf.fonttype': 42, 'ps.fonttype': 42,
        'savefig.facecolor': 'white', 'figure.facecolor': 'white',
    })


def save_figure(fig, stem):
    stem = Path(stem)
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix('.png'), dpi=320, pil_kwargs={'optimize': True})
    fig.savefig(stem.with_suffix('.pdf'), dpi=450,
                metadata={'Creator': 'SeismoAgentBench', 'CreationDate': None, 'ModDate': None})
