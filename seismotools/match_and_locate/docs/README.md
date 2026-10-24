# Match&Locate documentation

- [core/AGENT_CONTRACT_CARD.md](core/AGENT_CONTRACT_CARD.md) — what the tool
  produces, the case-level decisions it leaves to the caller, validity checks
  and failure meanings. Read first.
- [core/METHOD_NOTES.md](core/METHOD_NOTES.md) — the algorithm as implemented
  (correlation, linear moveout, per-node MAD statistics, de-duplication,
  magnitude), its approximations with numbers for a local network, and the
  measured cost on this host.
- [../runtime/python/MatchLocatepy/docs/MATCHLOCATEPY_CARD.md](../runtime/python/MatchLocatepy/docs/MATCHLOCATEPY_CARD.md)
  — Python preparation sequence and the rules the native program does not check.
- [../source/patches/README.md](../source/patches/README.md) — local patches
  and the evidence behind them.
- Upstream material: `../source/upstream/README.md`, the user guide and the
  three method/application papers (`../source/upstream/MatchLocate2.0_userguide.pdf`,
  `../source/upstream/doc/ZhangWen2015{GJI,GRL,SRL}.pdf`; local copies, not
  committed).

Use Match&Locate after a seed catalog exists (located events with picks or
reliable model travel times) and when the goal is completeness below the
detection floor of picking-based workflows or locations of small events
relative to well-located templates. It does not replace absolute location
of the templates or relative relocation of the final catalog.
