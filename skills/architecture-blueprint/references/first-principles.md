# First Principles

Pattern-free foundation. Every rule in this skill is derivable from here. Use this file when no decision rule covers the situation: derive the answer from these principles instead of importing a pattern. This is the rationale layer — the normative rules stay in SKILL.md and the other references. (Keyword conventions: see SKILL.md.)

## The frame: design is the assignment of proof obligations

Every correctness property is a proposition someone must discharge: *this value is well-formed, this state is legal, this actor is permitted, this resource is live, this operation happened once.* These obligations are conserved — the essential ones cannot be destroyed, only assigned. Design does not decide *whether* they get paid; it decides **who pays, when, how often, and in what currency**. From cheapest to most expensive:

1. **The machine, at construction, once** — structurally impossible to skip.
2. **One author, at one place, once** — and recorded.
3. **Every maintainer, at every use, forever** — from memory, unrecorded.

Nearly every rule in this skill moves obligations up this ladder. The canonical failure is validation that produces no change in representation: the obligation was discharged, but the payment left no receipt. To every later observer the value's epistemic state is unchanged, so the obligation regenerates at each use site — cost *nC*, paid in the most expensive currency there is: distributed human memory.

## The axiom

**Every reasoner that maintains the system — human or machine — has bounded capacity.** Correctness that depends on unbounded recall of unrecorded facts is not correctness; it is a debt whose default date is unknown. Everything below is a consequence of taking this seriously.

## The principles

### 1. Knowledge exists only where representation changed

A fact established without changing the value's representation lives only in the transient context of whoever established it — and contexts are not shared; for every later observer it reverts to *unknown*. Establishing `P(x)` SHOULD therefore be a transformation `x → x_P` such that possession of `x_P` entails `P`: the proof becomes a persistent object, not an event.

*Qualification:* encoding has a cost. It is justified when the fact is consumed more than once and stays valid across the region where `x_P` travels. A fact used once, immediately, at its point of establishment needs no vessel.

→ Here: parse-don't-validate, newtypes, value objects (`domain-modeling.md`).

### 2. Every fact has a validity frame

No fact is absolute; it holds relative to a frame — a process, a version of the rules that checked it, a trust domain, sometimes an instant. Carried across a frame boundary, `x_P` is not a proof but a claim. Preserve facts aggressively **within** frames, re-establish them **at** crossings, and make the crossings explicit objects of design — that is what a boundary *is*. The errors are symmetric: re-proving inside a frame wastes *nC*; trusting across a frame trades correctness for the *illusion* of a receipt, which is worse than none.

→ Here: module boundaries and public APIs, `Actor` resolved at the edge, declared consistency models, anti-corruption boundary.

### 3. Distinctions must exist in the medium, not the mind

Two things that mean different things but are represented identically differ only in human memory — so the machine permits every confusion between them. A convention is a request; structure is a constraint. Contrapositive, equally binding: a distinction with no consequence for correctness does not earn a representational difference. Encode the distinctions correctness *turns on*, and only those.

→ Here: newtypes for ids; the earn-it rule for every abstraction.

### 4. Match the representable to the meaningful

The ideal representation is a bijection between representable states and meaningful situations. Two failure directions:

- **Excess** (representable ⊃ meaningful): surplus illegal states every reader must rule out and every writer might construct.
- **Deficit** (representable ⊂ meaningful): real situations with no honest encoding get smuggled in through convention, overloading, or out-of-band memory — violating principle 3 by construction.

So the rule is NOT "minimize the state space." It is: *close the gap from above, and never cross below.* Compressing past the domain's real variety does not remove complexity; it relocates it into the most expensive currency.

→ Here: make illegal states unrepresentable, typed unions, temporal fields instead of status inference.

### 5. Interaction, not size, is the measure of complexity

Understanding cost grows with the pairs that can affect each other — edges, not nodes. A large sparse graph is cheaper than a small dense one. And the effective edge set exceeds the declared one: **whatever is observable will eventually be depended upon.** Every observable distinction — behavior, timing, ordering, error detail — becomes de facto contract. Minimize the *observable* surface, not merely the declared interface.

→ Here: narrow module APIs, acyclic dependencies, vertical slices (locality removes edges).

### 6. Authority defines interference

A component's authority is the set of states it can influence; components interfere only where authorities intersect. Authority in excess of responsibility purchases nothing and enlarges every intersection — pure liability. Limiting case: **every mutable fact SHOULD have exactly one authority.** One writer makes a fact's history a sequence; many writers make it a negotiation, and every reader must model the negotiators.

→ Here: state ownership, capability-oriented dependencies, `can*` policies (authority over actions made explicit).

### 7. Hidden inputs falsify the signature

If the visible signature is `f(x)` but behavior depends on time, ambient state, identity, or chance, reality is `f(x, t, g, i, r)` — and all reasoning from the visible signature is about a *different function*. This is not a demand to expose implementation; it is a prohibition on invisible semantics: any variable that changes correctness MUST appear in the reasoning model. What may stay hidden is exactly what changes nothing.

→ Here: functional core (pure logic), clock/id-generator as injected substrate, composition root (dependencies received, not reached for).

### 8. Uncertainty decreases monotonically inward

A healthy system is a monotone ascent: data gains constraint at each inward step and never silently loses it. A sick system carries raw ambiguity to its center, so every interior component re-confronts what the perimeter failed to resolve. Irreducible uncertainty — the world, other parties, the clock, the network — cannot be eliminated, but it can be *quarantined*: converted at the perimeter, once, into internal facts or explicit internal failures. Each semantic crossing SHOULD transform meaning **once**; repeated round-trips between representations are evidence the system never decided what it internally believes.

→ Here: boundary parsing (extractors), typed config at startup, translator at the gateway.

### 9. Failure is information with a frame

A failure is a fact at the level where it occurred, and principle 2 applies fully. Propagated raw, it leaks mechanism into contexts that cannot act on it; swallowed, it destroys information some frame needed. Handling is *translation at each frame crossing*: preserve exactly the semantics the receiving frame can act on, discard exactly the mechanism it cannot. A failure travels precisely as far as its meaning — no further, no less.

→ Here: the error taxonomy (`domain-modeling.md`).

### 10. Give operations an algebra the environment cannot break

Concurrent and distributed environments cannot promise exactly-once, in-order, ungrouped delivery. Correctness there MUST NOT depend on promises the environment cannot make; the resolution is algebraic — idempotence (`f∘f = f`) makes duplication harmless, commutativity makes reordering harmless, associativity makes regrouping harmless. **When delivery guarantees are weak, strengthen the algebra until the weakness is unobservable.** This is principle 1 applied to time.

→ Here: idempotency requirements, event handlers, consistency declarations.

### 11. Lifetime is a fact like any other

"This resource is still valid" is a proposition obeying principle 1. Left in convention — *remember to release, remember not to use after* — every use site pays from memory. Encoded structurally, as enclosure of the resource's lifetime within its owner's, release becomes a consequence of structure and use-after-invalidity becomes unrepresentable. Temporal validity is the fact most often left implicit, because it is invisible at any single instant — which is exactly why it most needs a receipt.

→ Here: state ownership, scope-bound resources, lifecycle typestate, cancellation propagation.

### 12. Quality is measured under counterfactual change

A system is its derivative, not only its behavior: for each assumption *A*, when *A* changes, how much changes with it? Keep `∂System/∂A` small for assumptions that actually vary — group by *shared reasons for change*, separate what must remain true from how it is currently achieved. *Essential qualification:* insulation is bought with edges and indirection (principle 5), so buy it ONLY against changes with real probability mass. The derivative is weighted by the distribution of actual change — not by the space of imaginable change.

→ Here: optimize-for-change, vertical slices, the Evolution Path, every "earn it" rule, no repository for a hypothetical DB swap.

### 13. Local checkability is the target all of this serves

The maintainer is a bounded prover. A design is good precisely insofar as each important property is verifiable from a context that fits in bounded attention, without opening every adjacent implementation. Guarantees must compose: `A ⇒ B` beside `B ⇒ C` yields `A ⇒ C` from contracts alone. When verifying a property requires the transitive closure of the system, the design has failed the axiom, whatever its other virtues. Every prior principle is a mechanism for this one.

→ Here: the North Star ordering (correctness, then comprehensibility), module READMEs as contracts, colocated tests, fitness functions.

## Compression

Three conserved reductions and one direction of flow:

- **Reduce possibility** — fewer representable-but-meaningless states (4), fewer distinctions living only in minds (3), fewer futures in which a fact must be re-proven (1, 11).
- **Reduce interaction** — fewer edges, declared and observable (5); smaller authority intersections (6); no invisible participants in any contract (7).
- **Reduce propagation** — uncertainty resolved at the perimeter and not re-imported (8); failure traveling exactly as far as its meaning (9); change absorbed near its source (12); environmental disorder absorbed by algebra (10).

**One direction:** correctness migrates *toward construction* — as early, as structural, as machine-checked as the domain permits; uncertainty migrates *toward the perimeter* — as late, as explicit, as contained as reality demands. Each fact is established at the point of maximum knowledge and minimum cost, and preserved from there to every point of use — within its frame, never past it.

## The final statement

> **Design is the assignment of proof obligations. The best assignment discharges each obligation once, at the point of maximum knowledge, in the cheapest currency available — structure before record, record before memory — and issues a receipt that travels with the value to the edge of its validity frame, where the obligation is knowingly, explicitly, purchased again.**

> **A solved problem should leave a residue in structure. The measure of an architecture is how little must ever be proven twice — and how honestly it knows where its proofs expire.**
