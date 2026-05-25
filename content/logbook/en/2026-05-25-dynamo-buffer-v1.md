---
title: First thoughts on the dynamo buffer
date: 2026-05-25
related_project: dynamo-buffer
summary: Initial architecture ideas.
tags: electronics, bikepacking
---

These are the first notes for a dynamo-powered buffer system. The target is not a perfect universal charger yet; it is a practical V1 that can survive real bikepacking use and teach me where the electrical limits are.

## Initial Concept

The system should accept the variable output of a hub dynamo, protect itself from voltage spikes, charge an intermediate buffer, and provide a stable output for small electronics. It should also fail gracefully: if the bike is moving slowly, charging can pause without upsetting the connected device.

## V1 Analog Architecture

The first version should lean on analog building blocks. A bridge rectifier and clamp handle the dynamo input, then a conservative charge stage feeds the buffer battery. A downstream regulator provides the user-facing output.

The appeal of this version is that it can be tested section by section. I can measure the dynamo input, then the rectified rail, then charge behavior, and finally the output stability under a few realistic loads.

## Future Work

- Choose a buffer chemistry and capacity.
- Measure dynamo behavior at different speeds.
- Prototype the rectifier and protection stage.
- Decide whether status LEDs are enough for V1.
