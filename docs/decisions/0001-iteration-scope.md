# ADR 0001 — Scope this repo to Phases 1–3 only

**Date:** 2026-05-14
**Status:** accepted

## Context

Xilin's six-stage methodology spans literature review through high-fidelity Omniverse validation. Phases 4–6 require Fusion 360, AI-driven concept generation, and NVIDIA Isaac Sim — different tools, different compute, and a different review cadence.

## Decision

This repository covers **Phases 1–3 only**:
1. Starship baseline ABM in Nihonbashi scene
2. Heat-Support Robot concept + variable matrix
3. Initial A/B SUMO/ABM simulation with iterative feedback

Phase 4 (CAD), Phase 5 (re-simulation), and Phase 6 (Omniverse) happen in downstream repositories that consume the converged variable matrix from this repo.

## Consequences

- Repo stays small, runnable on a student laptop.
- Variable matrix becomes the contract between this repo and downstream.
- Heavy CAD and Omniverse files do not pollute git history.
- Phase 5 will need to re-import the matrix to verify macroscopic gains; we keep the matrix CSV stable.
