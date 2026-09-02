# First Principles

Pattern-free foundation with its derivation tree. Every rule in this skill is derivable from here. Use this file when no decision rule covers the situation: derive the answer from these principles instead of importing a pattern. This is the rationale layer — the normative rules stay in SKILL.md and the other references. (Keyword conventions: see SKILL.md.)

## The frame: design is the assignment of proof obligations

Every correctness property is a proposition someone must discharge: *this value is well-formed, this state is legal, this actor is permitted, this resource is live, this operation happened once.* These obligations are conserved — they cannot be destroyed, only assigned. Design decides **who pays, when, how often, and in what currency**. From cheapest to most expensive:

1. **The machine, at construction, once** — structurally impossible to skip.
2. **A mechanized check, at every change, automatically** — the test suite is the ledger of obligations structure could not absorb.
3. **One author, at one place, once** — and recorded.
4. **Every maintainer, at every use, forever** — from memory, unrecorded.

The ladder orders coverage as well as cost: structure binds all cases, a check binds only the cases it states, a record binds only its reader, memory binds no one reliably.

One constraint governs the whole exercise: **an obligation must exist before it is assigned.** Discharging propositions no one relies on is negative work — every speculative proof is paid in real currency against a debt never owed. (This is the ground of every "earn it" rule in this skill.)

The canonical failure is validation that produces no change in representation: the obligation was discharged, but the payment left no receipt, so it regenerates at every use site — cost *nC*, paid in the most expensive currency there is: distributed human memory.

## The axioms

- **A1 — Reasoners are bounded.** Every mind maintaining the system — human or machine — has finite capacity. Correctness depending on unbounded recall of unrecorded facts is a debt with an unknown default date.
- **A2 — Minds are not shared.** The establisher of a fact and its later consumers are different minds with no common context; nothing transmits between them except persistent representation — of the value, or of evidence attached to it.
- **A3 — Essential obligations are conserved.** What a domain genuinely requires cannot be made to disappear by representation — only discharged, delegated, or relocated. Whatever appears eliminated has been moved; the only question is whether the move was priced.

## The principles

### 1. Knowledge exists only where representation changed

A fact established without changing the representation lives only in the establisher's transient context; by A2 it reverts to *unknown* for every later observer. Establishing `P(x)` SHOULD be a transformation `x → x_P` such that possession of `x_P` entails `P` — the proof becomes a persistent object, not an event. "Representation" includes evidence traveling attached to the value (a wrapper, a certificate, a token); what does not count is a proof that stays behind. *Qualification:* encoding has a cost; it is justified when the fact is consumed more than once within its validity region. A fact used once, at its point of establishment, needs no vessel.

- **Establish by transformation, not by inspection** — checking and passing the original onward transmits nothing.
- **Construction is the only path to possession** — if a strong value can be obtained without the proof, the receipt is forgeable.
- **Never require the same proof twice** within a fact's validity frame.
- **Pay at the earliest stable point** — greatest knowledge, fewest consumers: *C* instead of *nC*.
- **Information accumulates monotonically** — a step that knows more than its input outputs a representation carrying more, never less.
- **Do not decay strong representations casually** — each step back down the ladder re-creates every obligation the climb discharged.
- **A stored decision beats a repeated decision** — a rule decided identically at many sites is a fact awaiting its representation.
- **Execution leaves receipts too** — history that leaves no representation is reconstructed later by an investigator, in the worst currency at the worst time. These are *promised* observations for a named audience, not the incidental surface principle 5 minimizes.

→ Here: parse-don't-validate, newtypes, value objects; rung 2 → tests and fitness functions; execution receipts → observability and correlation IDs.

### 2. Every fact has a validity frame

No fact is absolute: it holds relative to a process, a version of the rules, a trust domain, sometimes an instant. Crossing a frame, `x_P` remains a proof only if the receiving frame can verify its evidence against its own trust anchors; otherwise it is a claim. Preserve facts aggressively **within** frames, re-establish **at** crossings, and make crossings explicit objects of design — that is what a boundary *is*. The errors are symmetric: re-proving inside a frame wastes *nC*; trusting across one buys the *illusion* of a receipt, worse than none.

- **What crosses a boundary is untrusted until accepted** — bookkeeping, not pessimism.
- **Evidence can travel; acceptance cannot** — a signature or capability discounts the crossing (verification fee instead of full re-proof) but never exempts it.
- **Structural reconstruction is not semantic proof** — deserializing recovers syntax; the domain's propositions are a second frame with its own entry proof.
- **Rules are part of the frame** — a fact proven under version *n* is a claim under *n+1*; stored receipts age.
- **Trust follows custody** — data that left and returned has crossed a frame even if it "was yours"; provenance is not proof.
- **Make crossings few, explicit, and load-bearing** — a design that knows its crossings concentrates all re-proof there.
- **The clock is a frame** — freshness, validity windows, and leases expire like any framed fact (see 12).
- **The checker bounds the proof** — "structurally impossible" means impossible within the enforcing mechanism's power, no further.

→ Here: module boundaries and public APIs, `Actor` resolved at the edge, anti-corruption boundary, declared consistency models.

### 3. Distinctions must exist in the medium, not the mind

Two things meaning differently but represented identically differ only in memory — so the machine permits every confusion between them. A convention is a request; structure is a constraint. Contrapositive, equally binding: a distinction with no consequence for correctness does not earn a representational difference.

- **Constraints by construction beat conventions by discipline** — only "there is no incorrect use to make" survives A1.
- **Semantic difference demands representational difference — where correctness turns on it**; without the qualifier every nuance breeds ceremony.
- **Names, comments, and documents are testimony, not enforcement** — whatever they alone protect is protected by nothing.
- **An abstraction must remove possibilities, not rename them** — ten concepts behind new vocabulary are still ten concepts.
- **The implicit obligation is the expensive one** — converting unstated preconditions into explicit structure is the standing direction of good design.

→ Here: newtypes for ids; the earn-it rule for every abstraction.

### 4. Match the representable to the meaningful

Close the gap between representable states and meaningful situations — from above, never crossing below. Several encodings of one meaning are legitimate at the perimeter; past it, the interior canonicalizes to one representative per meaning (see 8). Two failure directions:

- **Excess** (representable ⊃ meaningful): surplus illegal states every reader must rule out and every writer might construct.
- **Deficit** (representable ⊂ meaningful): real situations with no honest encoding get smuggled in through convention — violating principle 3 by construction.

So the rule is NOT "minimize the state space"; compressing below the domain's variety evicts complexity into convention, the most expensive residence there is.

- **Make illegal states unrepresentable** — a case that cannot be constructed needs no test, no branch, no memory.
- **Mutual exclusivity is an alternative, not a conjunction** — exclusive states as independent flags manufacture 2ⁿ worlds for *k* meanings.
- **Absence is a state, not a hole** — "not yet," "not applicable," "unknown" deserve honest encodings, not sentinels.
- **Exhaustiveness should be checkable** — then adding a case redistributes obligations automatically.
- **Meaningful stages deserve distinct states** — one undifferentiated representation forces every operation to carry the whole lifecycle's case analysis (see 12).

→ Here: typed unions, temporal fields instead of status inference, lifecycle typestate.

### 5. Interaction, not size, is the measure of complexity

Understanding cost grows with the pairs that can affect each other — edges, not nodes; a large sparse graph is cheaper than a small dense one. And the effective edge set exceeds the declared one: **given enough consumers and time, whatever is observably stable will be depended upon.** Corollary: an observable you refuse to promise is best made visibly unstable — dependence cannot form on what refuses to repeat.

- **Narrowness is worth more than smallness** — splitting a component while doubling mutual knowledge made things worse.
- **Depend on the least that suffices** — every dependency is an edge someone must one day rule out.
- **Compose narrow capabilities rather than accumulate broad ones** (see 6).
- **The observable surface is the real interface** — every stable observable not meant as a promise is an edge waiting to be discovered as load-bearing.
- **An interface states capability, not machinery** — exposed internals convert implementation detail into compatibility obligation.
- **Indirection is an edge, not a virtue** — a pass-through layer adds an edge and subtracts nothing.

→ Here: narrow module APIs, acyclic dependencies, vertical slices (locality removes edges).

### 6. Authority defines interference

A component's authority is the set of states it can influence; components interfere only where authorities intersect, and authority in excess of responsibility is pure liability. Limiting case: **every mutable fact needs one locus of authority — one writer, or, where several are necessary, one explicit resolution rule all of them submit to.** One writer makes a fact's history a sequence; many writers with no rule make it a negotiation every reader must model; many writers with a lawful merge (10) make it a sequence of resolutions.

- **Authority proportional to responsibility** — every reader must consider what a component *could* have done.
- **One writer per mutable fact, where practicable** — collapses an exponential space of interleavings into a line.
- **Where multiple writers are necessary, the resolution rule is the authority** — an ordering, a lawful merge, a designated arbiter.
- **One authoritative home per piece of knowledge** — a rule encoded in *n* places gives the system contradictory beliefs at the first divergent edit.
- **A redundant representation is a standing coherence obligation** — sound only while explicitly subordinate to the authoritative home and honest about staleness.
- **Shared mutable state is the maximal intersection** — prefer ownership, locality, immutability, or transfer of custody.
- **Decisions live with the authority over their subject** — an invariant guarded by every caller is guarded nowhere.
- **Exercising authority and reporting state are different acts** — separated, questions are free and changes are accountable.
- **Immutable by default** — mutability is a grant of authority and should be as deliberate as any other grant.

→ Here: state ownership, capability-oriented dependencies, `can*` policies, command/query separation, policies as the single home for a rule.

### 7. Hidden inputs falsify the signature

If the visible signature is `f(x)` but behavior depends on time, ambient state, identity, or chance, reality is `f(x, t, g, i, r)` — and all reasoning from the visible signature is about a *different function*. Not a demand to expose implementation; a prohibition on invisible semantics: what may stay hidden is exactly what changes nothing.

- **Receive dependencies; do not discover them** — a component handed its needs has a domain that can be read.
- **Time is an input** — the commonest hidden variable and the most routinely falsified signature.
- **Chance is an input** — where randomness affects outcomes, its source belongs in the reasoning model.
- **Identity, permission, locale, and configuration are inputs.**
- **No ambient authority** — globally reachable state connects all components pairwise through the back door (see 5, 6).
- **Determinism is the default; nondeterminism is a declared dependency** — visible as a named input, not embedded as a surprise.

→ Here: functional core, composition root, clock/id-generator as injected substrate.

### 8. Uncertainty decreases monotonically inward

A healthy system is a monotone ascent: data gains constraint at each inward step and never silently loses it; a sick system carries raw ambiguity to its center. Irreducible uncertainty — the world, other parties, the clock, the network — cannot be eliminated, but it can be *quarantined*: converted at the perimeter, once, into internal facts or explicit internal failures.

- **Resolve as early as correctness allows** — the earliest point has the fewest consumers and the most context. (Governs *data* uncertainty; *design* uncertainty obeys the opposite gradient — see 13.)
- **Normalize once, at the edge** — then the interior never learns the equivalence class existed.
- **One translation per crossing** — repeated round-trips between representations are evidence the system never decided what it believes.
- **The interior reasons over knowns** — logic reads as logic rather than as defense.
- **Separate calculation from interaction** — keeping the world at the rim keeps the harder problem out of the core's proofs (see 7).
- **Fail at the threshold, not in the interior** — viability uncertainty (missing config, absent prerequisites) resolved at startup, not detonated mid-flight.
- **Interior ambiguity is a smell of unfinished perimeter** — hedging deep in the system is interest on an obligation the boundary left unpaid.

→ Here: boundary parsing and extractors, typed config at startup, translator at the gateway.

### 9. Failure is information with a frame

A failure is a fact at the level where it occurred, and principle 2 applies fully. Propagated raw, it leaks mechanism into contexts that cannot act on it; swallowed, it destroys information some frame needed. Handling is *translation at each frame crossing*: preserve exactly the semantics the receiving frame can act on, discard exactly the mechanism it cannot.

- **Failure belongs in the contract** — an operation that can fail, presented as one that cannot, has a hidden output (7 applied to outcomes).
- **Failure is part of the operation's value space, however propagated** — any mechanism that removes failure from the reasoning model has exiled it, not handled it.
- **Distinct meanings of failure deserve distinct representations** — "impossible in this domain," "refused by policy," "the world did not cooperate" demand different responses (3 applied to errors).
- **Translate at each change of meaning; never leak, never swallow.**
- **Handle where understanding lives** — the frame that can distinguish retry from refusal from redesign decides; above it lacks context, below it lacks authority (see 6).
- **A failure's audience includes the future** — preserve the causal trail for the investigator, not just the caller.

→ Here: the error taxonomy (`domain-modeling.md`).

### 10. Give operations an algebra the environment cannot break

Environments with retries over unreliable links cannot promise exactly-once, in-order, ungrouped execution; correctness there MUST NOT depend on promises the environment cannot make. Resolution is algebraic — idempotence (`f∘f = f`) makes duplication harmless, commutativity makes reordering harmless, associativity makes regrouping harmless. **When delivery guarantees are weak, strengthen the algebra until the weakness is unobservable** — principle 1 applied to time.

- **Design for at-least-once, any-order** wherever duplication or reordering is possible.
- **Prefer idempotence wherever repetition is plausible** — then "did it already happen?" no longer needs an answer.
- **Identity of intent, not of message** — two arrivals of one intention must be recognizable as one intention.
- **Interruption is a first-class outcome** — "stopped partway" is a state every operation may enter (see 12).
- **Bound the unbounded** — an explicit bound fails predictably; an implicit one fails catastrophically.
- **Overload must propagate backward, not accumulate** — pressure that pools in the middle chooses its failure point at random.

→ Here: idempotency, event handlers, bounded fan-out, cancellation as a designed outcome.

### 11. Invariants have a consistency scope

An invariant rests on a set of facts that form one epistemic unit — meaningful only where its facts are witnessed together. The scope within which those facts change indivisibly is a first-order design object. Two symmetric errors: an invariant quietly straddling its scope is already broken, merely unobserved; a scope wider than any invariant requires pays for indivisibility — the most expensive guarantee an environment sells — and receives nothing.

- **Jointly necessary facts change in one act — within the scope** (4 applied jointly).
- **The scope is exactly as large as its invariants demand** — indivisibility justified per invariant, never defaulted per convenience of storage or module.
- **Across scopes, agreement is a process, not a state** — the window of disagreement is a real, representable situation, not an embarrassment to hide.
- **Where indivisibility is impossible, intermediate states are real** — modeled, each has a meaning and a path forward or back; unmodeled, they are corruption pending discovery.
- **A reader spanning scopes sees a moment, not a truth** — conclusions composed across scopes must tolerate skew or observe within one scope (2 applied to reads).

→ Here: declared consistency models, direct-call vs. event, unit-of-work/transaction, rich-object trigger (b) — an invariant spanning operations names its scope.

### 12. Lifetime is a fact like any other

"This resource is still valid" is a proposition obeying principle 1: left in convention, every use site pays from memory; encoded as enclosure — the resource's lifetime contained within its owner's — release becomes a consequence of structure. Temporal validity is the fact most often left implicit because it is invisible at any single instant — exactly why it most needs a receipt.

- **Possession should imply validity** (1 applied to time).
- **Enclosure over adjacency** — `Lifetime(resource) ⊆ Lifetime(owner)` makes release structural; adjacency makes it a coincidence maintained by vigilance.
- **Release mirrors acquisition** — acquisition without a designated end is a leak that hasn't happened yet.
- **Initiated work is owned work** — concurrent work whose lifetime escapes its initiator is unreachable by cancellation, invisible to teardown, alive by accident.
- **Stages with different legal operations are different states** (4 applied to lifecycle).
- **Endings deserve the care of beginnings** — a system that knows how to stop exhibits the same principle as one that refuses to start wrong.

→ Here: state ownership, scope-bound resources, lifecycle typestate, cancellation propagation.

### 13. Quality is measured under counterfactual change

A system is its sensitivity to change: for each assumption *A*, when *A* changes, how much changes with it? Keep `ΔSystem/ΔA` small for assumptions that actually vary — group by *shared reasons for change*, separate what must remain true from how it is currently achieved. *Essential qualification:* insulation is bought with edges and indirection (5); the sensitivity is weighted by the distribution of **actual** change, not the space of imaginable change.

- **Couple by shared reasons for change** — likeness of kind is not likeness of fate.
- **Sameness is sameness of reason, not of text** — unifying resemblances that share no fate buys a permanent edge to eliminate a repetition that was never a repetition of knowledge.
- **Separate stable meaning from unstable mechanism** — fused, the volatile drags the stable through every revision.
- **Depend on what is required, not on what happens to be** — the incidental's rate of change is inherited with it.
- **Change should exhaust itself near its source** — propagation distance measures how far the assumption had leaked.
- **Insure against probable change, not imaginable change** — bought where change is real it is architecture; bought everywhere it is superstition.
- **Design decisions are themselves framed facts** — early commitments are made at the point of minimum knowledge (2 applied to the designer); while uncertainty is high, prefer assignments cheap to revise, and escalate structure on evidence, not anticipation.
- **Compatibility is a promise about sensitivity** — a stable interface commits that dependents' proofs survive the provider's evolution.

→ Here: optimize-for-change, vertical slices, the Evolution Path (advance ONLY on a concrete trigger is "escalate on evidence" verbatim), every earn-it rule.

### 14. Local checkability is the target all of this serves

The maintainer is a bounded prover (A1). A design is good precisely insofar as each important property is verifiable from a context that fits in bounded attention, without opening every adjacent implementation. The hierarchy stated plainly: the ultimate objective is **minimizing the lifetime cost of keeping the system's propositions true**; local checkability is its dominant mechanism — and where they diverge, the objective wins.

- **Contracts must compose** — `A ⇒ B` beside `B ⇒ C` yields `A ⇒ C` from contracts alone; where they don't, every whole is re-proven from scratch.
- **Minimize simultaneously required context** — three independent assumptions beat ten entangled ones categorically.
- **What is needed to verify a thing should live near the thing** — locality of evidence is half of local checkability.
- **An interface is the complete list of what may be relied upon** — correct use requiring unstated knowledge means proofs resting on excavation (3 applied to contracts).
- **Modularity is proof-independence** — everything else called modularity is topology.
- **Understandability is load-bearing** — a design too costly to verify will be maintained unverified (A1).

→ Here: the North Star ordering, module READMEs as contracts, colocated tests, fitness functions.

## Where the principles collide

Real design is the adjudication of these conflicts; a framework that pretends otherwise is a liturgy.

- **Encoding hardens (1 vs 13)** — a fact paid into structure is cheap to consume and expensive to revise. Encode where consumption is frequent and the rule stable; keep the volatile in data or policy.
- **Today's variety vs tomorrow's (4 vs 13)** — the fit between representation and meaning is a target tracked over time, not achieved once.
- **Receipts vs surface (1 vs 5)** — resolved by a distinction, not a compromise: promised observations for a named audience vs incidental observability; maximize the first's usefulness, minimize the second's existence.
- **Resolve early vs commit late (8 vs 13)** — data uncertainty collapses at the perimeter as early as possible; design uncertainty collapses as late as responsibility allows. Opposite gradients for different unknowns; confusing them produces a defensive interior or a premature architecture.
- **Indivisibility vs liveness (11 vs 10)** — every fact added to a consistency scope is availability spent; the invariant must be worth its scope.
- **Single home vs performance (6 vs the world)** — redundant copies are resolved honestly only by pricing the coherence obligation into the decision.

No principle is absolute outside its conditions. The arbiter is the frame: compare total lifetime discharge cost under the *actual* distribution of use, change, failure, and uncertainty. When two principles collide, at least one is defending an obligation smaller than it looks — the work is finding which.

## The limits of the framework

- The quantities — consumption counts, change probabilities, edge weights — are judgments in notation's clothing; the formalism organizes judgment, it does not replace it.
- Structure-currency is not free, and over-paying is the signature failure: a framework this generative will happily generate proofs no one needed. The constraint stands: an obligation must exist before it is assigned.
- Enforcement is bounded by the enforcer: structure holds the weak propositions; the deep invariants of a domain still rest on the lower rungs, and honesty about which rung holds which proposition is part of the design.
- The scope is correctness economics only — silent on whether the system is worth building, fast enough, humane to operate, or good for the people it touches.

## The tests

The operational payoff — questions to ask of any design:

1. **Which obligation does this discharge — and does anyone actually hold it?**
2. **What obligation did this choice eliminate, and what new obligation did it create?**
3. **Who paid before, who pays after — in what currency, how many times?**
4. **Where is the receipt, and where does it expire?**
5. **What became unrepresentable — and did anything meaningful become unrepresentable with it?**
6. **What edges did this add, and what change do they insure against, with what probability?**
7. **Which invariant does this protect, and does its whole fact-set live inside one scope?**
8. **What happens when this runs twice, out of order, halfway?**
9. **Can the property this establishes be verified without leaving the room?**

A design that answers these well needs no pattern vocabulary to defend itself; a design that cannot answer them is not saved by one.

## Compression

Three conserved reductions and one direction of flow:

- **Reduce possibility** — fewer representable-but-meaningless states (4), fewer distinctions living only in minds (3), fewer unmodeled joint states and halfway worlds (11), fewer futures in which a fact must be re-proven (1, 12).
- **Reduce interaction** — fewer edges, declared and observable (5); smaller authority intersections (6); no invisible participants in any contract (7).
- **Reduce propagation** — uncertainty resolved at the perimeter and not re-imported (8); failure traveling exactly as far as its meaning (9); change absorbed near its source (13); environmental disorder absorbed by algebra (10); partial change contained within its scope (11).

**One direction:** correctness migrates *toward construction* — as early, as structural, as machine-checked as the domain permits; uncertainty migrates *toward the perimeter* — as late, as explicit, as contained as reality demands. Each fact is established at the point of maximum knowledge and minimum cost, and preserved from there to every point of use — within its frame, never past it.

## The final statement

> **Design is the assignment of proof obligations. The best assignment discharges each obligation once, at the point of maximum knowledge, in the cheapest currency available — structure before record, record before memory — and issues a receipt that travels with the value to the edge of its validity frame, where the obligation is knowingly, explicitly, purchased again.**

> **A solved problem should leave a residue in structure. The measure of an architecture is how little must ever be proven twice — and how honestly it knows where its proofs expire.**
