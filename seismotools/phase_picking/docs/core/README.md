# Phase-picking core documentation

This directory contains the method and interface notes needed to use the local phase-picking models. The executable benchmark entry points are in `../../interface/`; the model implementations and weights are in `../../source/` and `../../runtime/weights/`.

Use [`../examples/README.md`](../examples/README.md) as the model-usage guide and read the corresponding executable example in `../../examples/` before adapting an inference workflow. Case workflows must document channel order, sample rate, preprocessing, windowing, probability thresholds and conversion from probabilities to picks.
