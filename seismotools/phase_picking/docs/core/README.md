# Phase-picking core documentation

This directory contains the method and interface notes needed to use the local
phase-picking models. The executable benchmark entry points are in
`../../interface/`; the model implementations and weights are in
`../../source/` and `../../runtime/weights/`.

The model reference scripts and notebook are kept under `../examples/`. They
show inference conventions and are not complete event-detection workflows.
Case workflows must document channel order, sample rate, preprocessing,
windowing, probability thresholds, and conversion from probabilities to picks.
