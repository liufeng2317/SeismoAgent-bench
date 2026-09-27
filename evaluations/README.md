# Agent evaluations

This directory contains evaluation infrastructure, separate from scientific source preparation and the historical expert solution.

For current work, start with the [per-trial access development design](environment/ACCESS_DESIGN.md). The [architecture decision and audit](environment/ARCHITECTURE_REVIEW.md) documents the separate future formal-evaluation requirements. The [account utility runbook](environment/README.md) is retained for development only. The first implementation provides root-managed Unix-account isolation for a server already running inside a restricted container. It is not a Docker replacement or a hostile-code security sandbox.

Task definitions, agent adapters, RAG exposure policies and scientific scoring are not implemented here yet. The current environment runner executes a supplied command and records its artifacts; command success is not scientific task success.
