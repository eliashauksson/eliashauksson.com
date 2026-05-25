---
title: Dynamo Buffer System
slug: dynamo-buffer
date: 2026-05-25
status: in-progress
summary: A buffer battery and charging system for long-distance bikepacking.
tags: electronics, bikepacking, power
---

The Dynamo Buffer System is a small power electronics project for keeping devices charged during long-distance bikepacking. The idea is to turn the uneven output from a hub dynamo into a more predictable charging source, with enough buffering to ride through slow climbs, stops, and bad weather without constantly thinking about battery state.

![Placeholder system diagram](/static/img/projects/dynamo-buffer/placeholder.svg)

## Goals

- Capture useful energy from a bicycle hub dynamo.
- Buffer power so USB devices see a steadier supply.
- Keep the system compact, serviceable, and reliable on multi-day rides.
- Make the charging behavior understandable without a screen or app.

## Architecture

The first architecture uses a rectifier, input protection, a buffer battery stage, and a regulated output. The control logic should stay simple at first: prefer predictable analog behavior, then add measurement and smarter switching only where it clearly helps.

```text
Hub dynamo
  -> Rectifier and protection
  -> Charge control
  -> Buffer battery
  -> 5 V regulated output
  -> Phone, GPS, or lights
```

The main open question is how much capacity belongs in the buffer. Too little and the output drops often; too much and the system becomes heavier, slower to recover, and harder to package cleanly.
