<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright 2026 flxk1 -->
# Roadmap slice — the terminal surface and agentic oversight

Status: **draft, not committed scope.** Non-normative.

The console is a **client, not an engine**: all governance logic lives in RVND,
and this repository drives RVND's surface over MCP. Nothing in this slice changes
that. Every item is a surface over a decision made elsewhere.

The family roadmap is `RVND/docs/roadmap/agentic-oversight.md`; this slice covers
only what the terminal face owns.

---

## C1 · The oversight brief as a terminal surface

The scalability problem — a reviewer cannot read hundreds of intermediate steps,
and sampling them leaves blind spots — is usually treated as a limit of the
terminal. It is not. A terminal is a poor place to read a thousand actions and a
very good place to read the ten things a run could not settle.

If RVND exposes a bounded brief — unfired defeaters, contested premises,
undecided options, escalated gaps, mandate divergence — then the console is the
right surface for it, and arguably a better one than a canvas: it is where the
work is already happening, it is greppable, and it composes with everything else
in a shell.

*Candidate shape.* A `brief` command rendering the object RVND computes, ordered
so that root causes precede their consequences. The console adds no selection and
no ranking of its own; a client that decided which findings mattered would be
making a governance decision.

---

## C2 · Deterministic by default matters more here than anywhere

The console's existing discipline — chat routes through RVND's governance engine,
no model unless a provider is connected, and a connected model only *phrases*
RVND's result, never routes or decides — is exactly the property an oversight
surface needs.

The reason is specific rather than general. Reported reasoning is an
unfalsifiable claim about a private mechanism, and a surface that lets a model
narrate an oversight finding is producing exactly that: fluent, plausible, and
grounded in nothing checkable. The existing rule already prevents it.

Two additions follow:

- a phrased finding is **marked as phrased**, so a reviewer can tell narration
  from the engine's own text;
- the deterministic text remains reachable for any phrased finding — the
  fallback-on-error behaviour that already exists, made available on demand
  rather than only on failure.

---

## C3 · Intervention belongs on the surface the operator already has

Meaningful control requires that a person can actually intervene, and
intervenability is worth little if it lives one context-switch away. If RVND
supports pausing an agent, revoking a delegation, or narrowing an autonomy level,
those belong on the surface the operator is already looking at when they see the
finding that prompts them.

*Candidate shape.* Intervention commands over the existing MCP seam, with the
verdict shown as RVND returns it. The console proposes nothing and decides
nothing; it routes an operator's instruction and displays the answer.

*Constraint.* A revocation issued from the console must reach work already
running, or the surface is promising a control it does not deliver. That is
RVND's guarantee to provide; the console must not offer the command before it
holds.

---

## C4 · Show the chain, and where it roots

An operator reviewing an action taken several delegation hops away needs to see
the chain: who delegated to whom, under what mandate, and whether it roots in a
person.

The board view already renders workspaces and security state. A chain view is the
same idiom over data RVND projects, and the property most worth making obvious in
a terminal is the one easiest to lose in a diagram: **whether a chain terminates
in a human at all.**

---

## C5 · The measurement condition

The finding that motivates this work is that action traces raise reviewer
confidence without improving error detection. A terminal surface is not exempt —
a dense, authoritative-looking terminal output is a particularly effective way to
produce unearned confidence.

Every surface in this slice is therefore subject to the family's condition: it
ships with an error-detection measurement, or it does not ship, and rising
confidence without rising detection is recorded as a failure of the surface.

---

## Sequencing

| Step | Item | Depends on |
|---|---|---|
| 1 | C2 | nothing — tightens an existing discipline |
| 2 | C1 | RVND exposing a brief over MCP |
| 3 | C4 | RVND projecting the principal chain |
| 4 | C3 | RVND's revocation reaching running work |
| 5 | C5 | the surfaces above existing |

## Gates

The console re-implements no engine logic: every item routes over MCP, and a
step that computes a verdict, ranks a finding, or decides an escalation has
turned the client into an engine and is wrong regardless of how useful it looks.
