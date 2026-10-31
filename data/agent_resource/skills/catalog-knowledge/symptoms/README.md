# Symptom playbook

Each entry starts from what the checker reports (a flag id, or a value in `measurements` or in a check's `details`) and gives: the candidate causes; how far the cause can be established from the data alone; the evidence or experiment that separates the causes, with what each cause predicts; and the repair at its source.

How far a cause can be established — the same three tiers throughout:

- **A — attributable from the data.** The error has a signature of its own (a fixed or round value, a quantised offset, one station, one phase, a step in time). A cheap check or recomputation settles it. Repair it.
- **B — attributable with an experiment.** Several causes give the same symptom; one controlled change (another representation of the model, another grid, leave one station or phase out, reprocess one period) separates them. Run the experiment before repairing; write down beforehand what each cause predicts.
- **C — not attributable without external information.** The error is shared by all stations or events and is absorbed by origin times, station terms or the magnitude constant: a velocity model that is wrong on average, the absolute level of a magnitude scale, events hidden in a mainshock's coda. No check sees it. Use knowledge before the symptom appears: [`not_visible.md`](not_visible.md).

The general rule behind the tiers: an error with structure can be traced through the redundancy of the data; an error common to everything cannot.

| Stage | File |
|---|---|
| data, picks, association, detection | [`data_picks_association.md`](data_picks_association.md) |
| location, relative relocation | [`location_relocation.md`](location_relocation.md) |
| magnitude, completeness | [`magnitude_completeness.md`](magnitude_completeness.md) |
| what no check sees | [`not_visible.md`](not_visible.md) |

Two habits make attribution much easier:

1. **Keep a record of what changed.** For every product, note the code, parameters, model and inputs that produced it. When a symptom appears, first ask what changed since the last product without it; most causes are found that way.
2. **Do not trust formal errors or RMS.** Reported location uncertainties are often several times too small, and a lower travel-time RMS can come from fewer picks or a wrongly identified phase. Neither is evidence that a product is right.
