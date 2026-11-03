# What no check sees

Some errors are shared by every station or every event. Origin times, station terms and the magnitude constant absorb them, so the catalog stays internally consistent and every check passes. They are often the largest errors left in a careful catalog. Handle them with knowledge, before any symptom, and report them as uncertainties.

## The velocity model

A 1-D model that is too fast or too slow on average, or a datum that does not match the stations, moves all depths and origin times together. The sign depends on the geometry: a model that is too fast, with stations farther than about 1.5 focal depths, pushes events deeper; a near-surface layer that is too fast pushes them shallower. Station corrections and origin times absorb part of it and hide the rest.

What to do:

1. **Use the regional model, the way it was meant to be used.** Look for a published 1-D model of the region (regional network models, local tomography studies, minimum 1-D models) before choosing a generic one. Use only values you have read in a source (a table, the text, or a figure digitised with its axes checked against values quoted in the text); if you cannot obtain them, say so and use a generic model with the near-surface method below — a model rebuilt from memory or from a verbal description is not the published model and must not carry its name. Then check three things before locating:
   - **Datum.** Find what the model's depths are measured from (sea level, the mean station elevation, the surface). Use that as the reference elevation and start the depth search there. A model whose top is placed at sea level when its depths are below the surface leaves every ray about one station elevation in rock that is too slow or too fast; at stations 1–2 km above sea level this moves all origin times by several tenths of a second.
   - **Layers or nodes.** A minimum 1-D model is a stack of constant-velocity layers; interpolating it as a gradient between its layer tops makes the near surface much faster than the model. Use the representation the model was built in, and compare the other one only as an alternative.
   - **The near surface.** Generic models (CRUST1.0, LITHO1.0, global 1-D) and many regional models have 5–6 km/s just below the stations. Sediments, basin fill and volcanic deposits are often 2–4 km/s over the top 1–3 km. A near surface that is too fast makes origin times late and moves depths; it is the most common cause of a shared origin-time bias. Where the geology has such a layer, build candidates with it (next section).
   Locators differ too: a HypoInverse CRH model ignores station elevations (stations sit at the model's top), while NonLinLoc honours them; the same model can give different origin times in the two.
2. **Compare representations, not only models.** The same model as steps and as a linear gradient between nodes can differ as much as two different models. Try both on the full catalog and compare them with `compare.py` (`../playbooks/decide_between_candidates.md`).
3. **Do not choose by residual.** A model that fits the picks better (lower RMS) is not shown to place events better; a model with more freedom fits better by construction, and a model with a too-fast near surface can fit better than a correct one.
   The same holds for the other reference-free measures (Wadati origin offset, travel-time intercept, S−P depths, share at the shallowest depth): see the next section for what they can and cannot tell.
4. **Report the sensitivity.** Relocating with other plausible models (checker `--model-ensemble`) gives how far depths and origin times depend on the model. Report it as an uncertainty; it does not tell which model is right.
5. **Independent information settles it:** explosions or quarry blasts with known locations and times, depth phases, events with geodetic or surface-rupture constraints, a well-located reference set. Use it where it exists and say when it does not.

## Constraining the near surface without a regional model

Where no regional model can be used, the near surface has to be set from geology and bracketed; the picks constrain it only weakly. This was tested offline on six recorded sequences: a generic column (CRUST1.0, Vs from the data's own Wadati Vp/Vs, its top at the mean station elevation) and the same column under a slow top layer of 1, 2 or 3 km at Vp 2.5, 3.5 or 4.5 km/s, each relocating the same 500 events, scored against independent catalogs. What follows is what held in those tests.

1. **Build the candidates from the geology.** Find what lies under the stations: sediment or basin-fill thickness, volcanic deposits, crystalline rock at the surface (geological maps, basin-depth and well studies, near-surface Vs studies). Make one candidate without a slow layer and two or three whose layers span the plausible thickness and velocity. Take Vs from the data's Wadati Vp/Vs, not from a textbook ratio, and put the model's top at the datum you locate with.
2. **The data give the direction, not the level.** Within one sequence a slower or thicker top layer moves the Wadati origin offset (checker `wadati_origin_offset`) toward positive and the origin times earlier, almost one for one (correlation −0.87 to −1.00 in five of six sequences, −0.34 in the sixth). But the Wadati offset of the best candidate differed between sequences (−0.5 to +0.1 s), so no target value exists. Among the sequences where some candidate was right, choosing the smallest Wadati offset, the lowest RMS or the smallest share at the shallowest depth chose a wrong candidate in one of three; the smallest travel-time intercept or S−P depth offset in two of three. Use these measures to check that a candidate moves the catalog the way the geology predicts; do not select by any of them.
3. **A slow layer is not a universal repair.** In half of the sequences no candidate brought origin times within 0.3 s and depths within 1 km; the remaining error came from elsewhere (deeper structure, the locator, the picks). If a shared origin-time or depth shift you attribute to the near surface hardly changes across the geologically plausible candidates, look elsewhere.
4. **Choose by the geology and report the spread.** Adopt the candidate the geological evidence supports, before looking at fit measures, and write down why. Report the range of origin times and depths over the candidates as an uncertainty (0.3–0.9 s and 0.6–5 km in these tests) and state that the near surface was not constrained by independent information.

## The absolute level of the magnitude scale

A magnitude scale whose distance correction or constant does not suit the region shifts all magnitudes by 0.1–0.4 units. Station terms and the constant trade off; the catalog is consistent with itself. Use the calibration of the region (`../../../magnitude/calibrations.json`), state which one, and where moment magnitudes of some events exist, compare with them.

## Events hidden in a mainshock's coda

In the first minutes after a large event every station is saturated with its coda. Pickers, associators and simple energy scans miss aftershocks there, including events of magnitude 4 and more after a magnitude-7 mainshock. No reference-free check finds them: nothing triggers.

What to do: after the largest events, reprocess the first tens of minutes with methods made for it — template matching with templates of the sequence, a picker with a lower threshold on high-frequency records, far stations whose coda is weaker — and mark the period as incomplete in the catalog with its estimated completeness Mc(M, t) = M − 4.5 − 0.75 log10(t / 1 day).

## Timing common to all stations, and constant station delays

A timing error shared by all stations moves every origin time and nothing else. A constant clock offset at one station is absorbed by its station correction, exactly like slow ground under it. Check the timing quality flags of the records and the station logs where available; otherwise state that absolute timing was not verified.
