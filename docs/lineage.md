---
type: Reference
title: Lineage
description: Honest limits and provenance.
---

# Honest limits

- The probe signs in with throwaway values on purpose. It measures the
  auth path, never a real credential.
- Probe output can carry sensitive material: service hostnames, fault
  internals, whatever the vendor's error pages leak. This repo gitignores
  `results.jsonl` and `notes.jsonl` for that reason. Treat them as
  incident evidence, not shareable output.
- One process, one schedule. This is an incident instrument you start when
  things break, not a monitoring platform.

# Lineage

This is a distillation, not a port. The original took shape in hours, in
the middle of a real outage. Every up/down monitor could answer "is it
down". None could answer "what changed". The layered shape, the classified
outcomes, and the verbatim-evidence rule all come from that night and from
the vendor case that followed. The vendor, the fault, and the timings stay
out of this repo on purpose — the example fault strings here are
inventions. An earlier home-network monitor taught the same lesson
smaller: up/down answers the wrong question.

Distilled: August 2026. This repository began at distillation. The dates
above describe the pattern's history, not this commit log.
