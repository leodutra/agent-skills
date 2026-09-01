# First Principles of Software Design — Extended

*A pattern-free extraction, with the full derivation tree. No pattern is named; every pattern should be derivable. Under each first principle stand the engineering principles it generates, each with its one-line derivation. Where a derived principle has two parents, it is listed under the dominant one and cross-referenced — the structure is a DAG that reads as a tree.*

---

## The frame: design is the assignment of proof obligations

Every correctness property of a system is a proposition someone must discharge: *this value is well-formed, this state is legal, this actor is permitted, this resource is live, this operation happened once.* These obligations are conserved — the essential ones cannot be destroyed, only assigned. Design does not decide *whether* they get paid; it decides **who pays, when, how often, and in what currency**.

The currencies are not equal. Ordered from cheapest to most expensive:

1. paid by the machine, at construction, once — structurally impossible to skip;
2. paid by a mechanized check, at every change, automatically — the test suite is the ledger of obligations structure could not absorb, re-audited on demand;
3. paid by one author, at one place, once — and recorded;
4. paid by every maintainer, at every use, forever — from memory, unrecorded.

The ladder orders coverage as well as cost: structure binds all cases, a mechanized check binds only the cases it states, a record binds only the reader who reads it, and memory binds no one reliably.

One constraint governs the whole exercise: **an obligation must exist before it is assigned.** Discharging propositions no one relies on is not diligence but negative work — every speculative proof is paid in real currency against a debt that was never owed.

The central failure mode is a payment in the wrong currency:

> **Validation that produces no change in representation leaves the burden on every future caller.**

The obligation was discharged — but the payment left no receipt. To every later observer the epistemic state of the value is unchanged, so the obligation regenerates at every use site. The cost is not *C* but *nC*, paid in the most expensive currency there is: distributed human memory.

---

## The axioms

Three assumptions carry everything below; deny any one and the framework dissolves.

**A1 — Reasoners are bounded.** Every mind that maintains the system — human or machine — has finite capacity. Correctness that depends on unbounded recall of unrecorded facts is not correctness; it is a debt whose default date is unknown.

**A2 — Minds are not shared.** The reasoner who establishes a fact and the reasoners who later depend on it are different minds, at different times, with no common context. Nothing transmits between them except persistent representation — of the value itself, or of evidence attached to it: a certificate, a signature, a capability are representations too. This is why receipts exist at all.

**A3 — Essential obligations are conserved.** The propositions a domain genuinely requires cannot be made to disappear by representation; they can only be discharged, delegated, or relocated. Design chooses their assignment, never their existence; whatever appears eliminated has been moved, and the only question is whether the move was priced.

---

# The principles

## 1. Knowledge exists only where representation changed

An observer's knowledge of a value is a function of the value's representation and the observer's context. When a fact is established but the representation is unchanged, the fact lives only in the transient context of whoever established it — and by A2, contexts are not shared. For every later observer the fact's status reverts to *unknown*.

Therefore establishing a fact `P(x)` should be a transformation `x → x_P` such that possession of `x_P` entails `P`. The proof becomes a persistent object rather than an event. "Representation" is broad here: the change may be in the value's own shape or in evidence that travels attached to it — a wrapper, a certificate, a token. What does not count is a proof that stays behind: a fact whose evidence is not recoverable from what the consumer holds has, for that consumer, never been established.

*Qualification:* encoding has a cost, so it is justified when the fact will be consumed more than once and remains valid across the region where `x_P` travels. A fact used once, immediately, at its point of establishment, needs no vessel.

**Under it:**

- **Establish by transformation, not by inspection.** Checking a property and passing the original onward transmits nothing; only a changed representation transmits — so the act of proving and the act of strengthening the representation should be one act.
- **Construction is the only path to possession.** If a strong value can be obtained without passing through the proof, the representation lies; the proving path must be the sole path, or the receipt is forgeable.
- **Never require the same proof twice.** Within a fact's validity frame, re-checking an already-carried fact adds no information — it only re-imposes a discharged obligation, converting a paid debt back into an outstanding one.
- **Pay at the earliest stable point.** An obligation discharged where knowledge is greatest and consumers are fewest costs *C*; deferred outward, it costs *nC* — so expensive facts (interpretation, normalization, permission, configuration) migrate to the earliest point where their result stays valid.
- **Information accumulates monotonically.** Learning and then discarding is regression; a transformation that knows more than its input should output a representation that carries more, never less.
- **Do not decay strong representations casually.** Each step backward down the certainty ladder re-creates every obligation the climb had discharged; descent should be deliberate, at frame boundaries, never as a convenience.
- **A stored decision beats a repeated decision.** Anything decided identically at many sites — a rule, a normalization, an interpretation — is a fact awaiting its representation; repetition of judgment is the mental-currency form of repeated proof (see also 6).
- **Execution leaves receipts too.** The running system continuously establishes facts — what happened, in what order, caused by what — and history that leaves no representation must later be reconstructed by an investigator, paid in the most expensive currency at the worst possible time. These receipts are *promised* observations, deliberately emitted for a named audience — not the incidental observability principle 5 tells you to minimize.

## 2. Every fact has a validity frame

No fact is absolute. It holds relative to a frame: a process, a version of the rules that checked it, a trust domain, sometimes an instant. `x_P` proves `P` *within the frame where the proof was made*. Carried across a frame boundary — into another process, another epoch of the rules, another party's custody — it remains a proof only if the receiving frame can recognize and verify its evidence against that frame's own trust anchors; otherwise it is a claim.

Therefore: preserve facts aggressively **within** frames (principle 1), re-establish them **at** frame crossings, and make the crossings themselves explicit objects of design. This is what a boundary *is*: the locus where established knowledge expires and must be repurchased. The two errors are symmetric — re-proving inside a frame wastes *nC*; trusting across a frame trades correctness for the *illusion* of a receipt, which is worse than no receipt.

**Under it:**

- **What crosses a boundary is untrusted until accepted.** Not as pessimism but as bookkeeping: whatever the departure state, the arrival state is what the receiving frame can itself verify — and where no portable evidence traveled, that is the bottom of the ladder.
- **Evidence can travel; acceptance cannot.** Portable evidence — a signature, a certificate, a capability — does not exempt the crossing, it discounts it: the receiving frame still performs an act of acceptance against its own trust anchors, paying a verification fee instead of full re-proof. The discount is worth serious engineering; the exemption is the illusion of a receipt.
- **Structural reconstruction is not semantic proof.** Recovering the *shape* of data from a wire form establishes syntax only; the domain's propositions form a second, separate frame that must be entered by its own proof.
- **Rules are part of the frame.** A fact proven under version *n* of the rules is a claim under version *n+1*; wherever rules evolve, stored receipts age, and the design must say what re-proof their expiry triggers.
- **Trust follows custody.** Data that leaves your custody and returns — through storage, a peer, a queue — has crossed a frame even if it "was yours"; provenance is not proof.
- **Make crossings few, explicit, and load-bearing.** Every crossing is a mandatory repurchase of knowledge; a design with accidental, implicit, or repeated crossings pays that price without noticing, and a design that knows its crossings can concentrate all re-proof there.
- **The clock is a frame.** Facts with temporal scope — freshness, validity windows, leases — expire like any other framed fact; an instant of proof is part of the proof (see also 12).
- **The checker bounds the proof.** "Structurally impossible" means impossible within the enforcing mechanism's power, and no further; claiming more than the checker verified is the illusion-of-receipt error committed against oneself.

## 3. Distinctions must exist in the medium, not the mind

If two things mean different things but are represented identically, the distinction exists only in human memory — and the machine will therefore permit every confusion between them. A convention is a request; structure is a constraint. Meaning that is not representable is not enforced, and by A1, anything enforced only by recall will eventually fail.

The contrapositive matters equally: a distinction that carries no consequence for correctness does not earn a representational difference.

**Under it:**

- **Constraints by construction beat conventions by discipline.** A convention says "please use this correctly"; a structural constraint says "there is no incorrect use to make" — and only the second survives the axiom.
- **Semantic difference demands representational difference — where correctness turns on it.** Two interchangeable-looking values with non-interchangeable meanings are an accident already scheduled; the qualifier is the whole principle, for without it every nuance breeds ceremony.
- **Names, comments, and documents are testimony, not enforcement.** They inform the willing reader and bind no one; whatever they alone protect is protected by nothing.
- **An abstraction must remove possibilities, not rename them.** Ten concepts behind new vocabulary are ten concepts; only an abstraction that makes some incorrect thing *inexpressible* has reduced the reasoning space rather than reorganized its syntax.
- **The implicit obligation is the expensive one.** Every unstated precondition is a distributed liability billed to all future participants; converting implicit obligation into explicit structure is the standing direction of good design.

## 4. Match the representable to the meaningful

Every representable state is a possibility some reasoner may one day have to exclude. The ideal representation closes the gap between representable states and meaningful situations: every representable state has a valid interpretation, and every distinction on which correctness turns has an honest representation. (Strict one-to-one correspondence is not the law — several encodings of one meaning are legitimate at the perimeter; but the moment they pass it, the equivalence class becomes an obligation every consumer must know, which is why the interior canonicalizes to one representative per meaning — see 8.) There are two failure directions, and the second is the one naive formulations miss:

- **Excess** — representable ⊃ meaningful: the surplus states are illegal, yet every reader must rule them out and every writer might construct them.
- **Deficit** — representable ⊂ meaningful: real situations of the domain now have no honest encoding, so they get smuggled in through convention, overloading, or out-of-band memory — violating principle 3 by construction.

So the principle is **not** "minimize the state space." It is: *close the gap between representable and meaningful from above, and never cross below.*

**Under it:**

- **Make illegal states unrepresentable.** The strongest handling of a bad case is its nonexistence; a case that cannot be constructed needs no test, no branch, and no memory.
- **Mutual exclusivity is an alternative, not a conjunction.** States that exclude each other, encoded as independent flags, manufacture 2ⁿ representable worlds for *k* meaningful ones — the excess is pure obligation.
- **Absence is a state, not a hole.** "Not yet," "not applicable," and "unknown" are meaningful situations; encoding them as sentinel values or overloaded members is the deficit direction wearing a disguise.
- **Exhaustiveness should be checkable.** If handling all representable cases can be mechanically confirmed, adding a case redistributes obligations automatically; if not, every addition silently creates unhandled worlds.
- **Meaningful stages deserve distinct states.** When a thing's legal operations differ across its life, one undifferentiated representation forces every operation to carry the whole lifecycle's case analysis (see also 12).
- **Do not compress below the domain's variety.** A representation smaller than the situation space it must express doesn't remove complexity — it evicts it into convention, the most expensive residence there is.

## 5. Interaction, not size, is the measure of complexity

The cost of understanding a system grows not with the number of parts but with the number of pairs that can affect each other — with edges, not nodes. A large sparse graph is cheaper than a small dense one.

And the effective edge set is larger than the declared one: **given enough consumers and time, whatever is observably stable will be depended upon.** Every stable distinction a component exposes — in behavior, timing, ordering, error detail — tends toward de facto contract, whether promised or not. The corollary: an observable you refuse to promise is best made visibly unstable, since dependence cannot form on what refuses to repeat.

**Under it:**

- **Narrowness is worth more than smallness.** Splitting a component in two while doubling their mutual knowledge has made things worse; the target of decomposition is fewer edges, not smaller boxes.
- **Depend on the least that suffices.** Each dependency is an edge someone must one day rule out; a component that receives the world can be affected by the world, and every reader must account for that.
- **Compose narrow capabilities rather than accumulate broad ones.** Assembly from parts that each touch little keeps the interaction budget linear; growth by accretion onto one part compounds it (see also 6).
- **The observable surface is the real interface.** Whatever can be noticed, and repeats, will be relied upon — so every stable observable not meant as a promise is an edge waiting to be discovered as load-bearing, and minimizing unintended observability is minimizing future contract.
- **An interface states capability, not machinery.** Exposed internals enlarge the observable surface for no semantic gain, converting today's implementation detail into tomorrow's compatibility obligation.
- **Indirection is an edge, not a virtue.** Every layer between intent and effect must buy its keep in removed possibilities or contained change; a pass-through layer adds an edge and subtracts nothing.

## 6. Authority defines interference

A component's authority is the set of states it can influence. Two components can interfere only where their authorities intersect; the total interference potential of a system is the sum of these intersections. Authority in excess of responsibility purchases nothing and enlarges every intersection it touches.

The limiting case is the most important: **every mutable fact needs one locus of authority — one writer, or, where several writers are necessary, one explicit resolution rule that all of them submit to.** Single ownership is the cheapest implementation of that rule, not the rule itself: with one writer the fact's history is a sequence; with many writers and no authoritative resolution it is a negotiation every reader must model; with many writers and a lawful merge (10) it is a sequence again — of resolutions.

**Under it:**

- **Authority proportional to responsibility.** Capability beyond need is liability without asset — it widens what the component *could* have done, and every reader of every interaction must consider what it could have done.
- **One writer per mutable fact, where practicable.** Reducing writers from *n* to one collapses an exponential space of interleavings into a line; the single most profitable reduction available in state management.
- **Where multiple writers are necessary, the resolution rule is the authority.** Concurrent writers without an explicit, total resolution rule are a negotiation with no chair; with one — an ordering, a lawful merge, a designated arbiter — authority has not been abandoned, only delegated to the rule (see also 10).
- **One authoritative home per piece of knowledge.** A rule encoded in *n* places has *n* independent authorities over one fact; the first divergent edit gives the system contradictory beliefs, and every reader thereafter must adjudicate which copy is true — an obligation paid in memory, forever.
- **A redundant representation is a standing coherence obligation.** Every deliberate second copy of knowledge — kept for speed, locality, or availability — reintroduces the divergence it was designed away from, and is sound only while an explicit discipline keeps it subordinate to the authoritative home and honest about its staleness (see also 2).
- **Shared mutable state is the maximal intersection.** Where many may write what many may read, everyone's assumptions are hostage to everyone's actions; prefer ownership, locality, immutability, or transfer of custody — each shrinks an intersection to a point.
- **Decisions live with the authority over their subject.** An invariant guarded by its owner is guarded once; an invariant guarded by every caller inspecting state and acting on it is guarded nowhere, since each such caller exercises borrowed authority without the owner's knowledge.
- **Exercising authority and reporting state are different acts.** An operation that both changes the world and answers a question makes every observation a potential interference; separated, questions are free and changes are accountable.
- **Immutable by default.** What cannot change cannot be interfered with; mutability is the grant of authority and should be as deliberate as any other grant.

## 7. Hidden inputs falsify the signature

A component's true domain is everything that materially affects its behavior. If the visible signature is `f(x)` but the behavior depends on time, ambient state, identity, or chance, then reality is `f(x, t, g, i, r)` — and every conclusion drawn from the visible signature is reasoning about a *different function*.

This is not a demand to expose implementation; it is a prohibition on invisible semantics. What may stay hidden is exactly what changes nothing.

**Under it:**

- **Receive dependencies; do not discover them.** A component that reaches into the ambient world for what it needs has inputs no signature declares; a component handed its needs has a domain that can be read.
- **Time is an input.** Behavior that varies with the clock while the clock is absent from the contract is nondeterminism presented as determinism — the commonest hidden variable and the most routinely falsified signature.
- **Chance is an input.** Same argument, same remedy: where randomness affects outcomes, its source belongs in the reasoning model, or the function's identity changes on every call unannounced.
- **Identity, permission, locale, and configuration are inputs.** Anything that makes the same visible call mean different things in different contexts is part of the true domain and must appear in it.
- **No ambient authority.** Globally reachable state is a hidden input to everything and a hidden output of everything — the densest possible edge, connecting all components pairwise through the back door (see also 5, 6).
- **Determinism is the default; nondeterminism is a declared dependency.** A computation whose outputs are a function of its stated inputs can be replayed, compared, and trusted; every departure from that should be visible as a named input, not embedded as a surprise.

## 8. Uncertainty decreases monotonically inward; the irreducible remainder stays at the perimeter

Order knowledge states by information: more constrained ⊒ less constrained. A healthy system is a monotone ascent — data gains constraint at each inward step and never silently loses it. A sick system carries raw ambiguity to its center, so every interior component re-confronts what the perimeter failed to resolve.

Some uncertainty is irreducible — the world, other parties, the clock, the network. It cannot be eliminated, but it can be *quarantined*: converted at the perimeter, once, into internal facts or explicit internal failures.

**Under it:**

- **Resolve as early as correctness allows.** Every inward step ambiguity survives multiplies its audience; the earliest point of resolution has the fewest consumers and the most context. (This governs uncertainty about *data*; uncertainty about the *design itself* obeys the opposite gradient — see 13.)
- **Normalize once, at the edge.** If equivalent inputs converge to one canonical form on entry, the interior never learns the equivalence class existed; deferred, every interior component must know it.
- **One translation per crossing.** Repeated round-trips between representations of the same information are evidence the system never decided what it believes — and each trip is a fresh opportunity for loss, drift, and duplicated rules.
- **The interior reasons over knowns.** The reward of a disciplined perimeter is a center that assumes its inputs are what they claim — where logic reads as logic rather than as defense.
- **Separate calculation from interaction.** Reasoning about values is one problem; reasoning about values *and* the world's cooperation is a harder one — keeping the world at the rim keeps the harder problem out of the core's proofs (see also 7).
- **Fail at the threshold, not in the interior.** Uncertainty about viability — missing configuration, absent prerequisites, unreachable essentials — resolved at startup is a fact established once at the earliest perimeter; deferred, it detonates mid-flight with the whole system as blast radius (see also 1).
- **Interior ambiguity is a smell of unfinished perimeter.** Wherever deep components hedge — re-checking, tolerating, guessing — the boundary above them left an obligation unpaid, and the hedging is its interest.

## 9. Failure is information with a frame

A failure is a fact about the world at the level where it occurred, and principle 2 applies to it fully. Propagated raw across frames, it leaks a mechanism into contexts that cannot act on it; swallowed, it destroys information that some frame needed. Neither is handling.

Handling is *translation at each frame crossing*: preserve exactly the semantics the receiving frame can act upon, discard exactly the mechanism it cannot.

**Under it:**

- **Failure belongs in the contract.** An operation that can fail, presented as one that cannot, has a hidden output (7 applied to outcomes); the possible outcomes of an operation are part of its meaning.
- **Failure is part of the operation's value space, however propagated.** Whether carried as data or as control transfer, failure must compose, translate, and remain visible to reasoning; the propagation mechanism is secondary, and any mechanism that removes failure from the reasoning model has not handled it but exiled it.
- **Distinct meanings of failure deserve distinct representations.** "Impossible in this domain," "refused by policy," and "the world did not cooperate" demand different responses; one undifferentiated failure forces every handler to reverse-engineer the taxonomy (3 applied to errors).
- **Translate at each change of meaning; never leak, never swallow.** Each frame receives the failure in its own vocabulary, no richer and no poorer than what it can act on — leakage exports mechanism, swallowing destroys evidence, translation preserves exactly the actionable remainder.
- **Handle where understanding lives.** The frame that can distinguish retry from refusal from redesign is the frame that should decide; handling above it lacks context, handling below it lacks authority (see also 6).
- **A failure's audience includes the future.** What is preserved through translation should serve not only the caller but the investigator — discarding the causal trail to tidy the interface trades tomorrow's diagnosis for today's neatness.

## 10. Give operations an algebra the environment cannot break

Some environments cannot promise that an operation runs exactly once, in order, ungrouped — most distributed settings are such environments at some layer, and any setting with retries over an unreliable link certainly is. Correctness there must not depend on promises the environment cannot make. The resolution is algebraic: choose operation semantics whose closure absorbs the environment's uncertainty.

- Idempotence — `f∘f = f` — makes duplication harmless.
- Commutativity makes reordering harmless.
- Associativity makes regrouping harmless.

**When delivery guarantees are weak, strengthen the algebra until the weakness is unobservable.**

**Under it:**

- **Design for at-least-once, any-order — wherever duplication or reordering is possible.** Exactly-once-in-order is a promise such environments keep only on good days; semantics that survive repetition and reordering convert delivery uncertainty from a correctness problem into a non-event.
- **Prefer idempotence wherever repetition is plausible.** When re-execution equals execution, the entire question "did it already happen?" — unanswerable in a distributed setting — no longer needs an answer.
- **Identity of intent, not of message.** Two arrivals of one intention must be recognizable as one intention; an operation that cannot recognize its own repetition will perform it.
- **Interruption is a first-class outcome.** In an environment that can abandon work at any point, "stopped partway" is a state every operation may enter; semantics that account for it degrade cleanly, semantics that ignore it corrupt quietly (see also 11).
- **Bound the unbounded.** The environment will not moderate itself — every queue, wait, retry, and concurrent demand grows until something breaks unless a bound is chosen; an explicit bound fails predictably where an implicit one fails catastrophically.
- **Overload must propagate backward, not accumulate.** When production exceeds consumption, the excess must slow the source rather than pool in the middle; a system that absorbs pressure silently is choosing its failure point at random.

## 11. Invariants have a consistency scope

An invariant rarely rests on one fact; it rests on a set, and that set forms a single epistemic unit — the invariant is meaningful only where its facts are witnessed together. The scope within which those facts change indivisibly, and outside which they may legitimately be observed apart, is a first-order design object, not an implementation detail.

Two errors are possible, and both are common. An invariant that quietly straddles its scope is already broken — the violation merely hasn't been observed yet. A scope drawn wider than any invariant requires pays for indivisibility — the most expensive guarantee an environment sells, priced in serialization, contention, and coupled availability — and receives nothing for it.

**Under it:**

- **Jointly necessary facts change in one act — within the scope.** Facts that an invariant binds together must move together where the invariant lives; movement one-at-a-time inside the scope manufactures states the domain never meant to exist (4 applied jointly).
- **The scope is exactly as large as its invariants demand.** Every fact added to a scope taxes every change within it; indivisibility must be justified per invariant, never defaulted per convenience of storage or module.
- **Across scopes, agreement is a process, not a state.** Where no single act can bind facts, their convergence takes time — and the window of disagreement is a real, representable situation, not an embarrassment to hide.
- **Where indivisibility is impossible, intermediate states are real.** The halfway points of a multi-scope change exist whether modeled or not — modeled, each has a meaning and a path forward or back; unmodeled, they are corruption pending discovery.
- **A reader spanning scopes sees a moment, not a truth.** Facts gathered from different scopes were established at different instants; a conclusion composed from them must tolerate their skew or arrange to observe within one scope (2 applied to reads).

## 12. Lifetime is a fact like any other

"This resource is still valid" is a proposition, and it obeys principle 1: if its truth lives in convention — *remember to release, remember not to use after* — every use site pays the obligation from memory. Encoded structurally, as an enclosure — the resource's lifetime contained within its owner's — release becomes a consequence of structure rather than a remembered duty.

Temporal validity is the fact most often left implicit, because it is invisible at any single instant. That is exactly why it most needs a receipt.

**Under it:**

- **Possession should imply validity.** If holding the handle proves the resource lives, the proof travels with every use (1 applied to time); if holding proves nothing, every use begins with an unanswerable question.
- **Enclosure over adjacency.** `Lifetime(resource) ⊆ Lifetime(owner)` makes release a structural consequence of the owner's own end; mere adjacency of lifetimes makes it a coincidence maintained by vigilance.
- **Release mirrors acquisition.** Whoever brought a resource into being — or whatever scope did — carries the symmetric duty of its end; acquisition without a designated end is a leak that hasn't happened yet.
- **Initiated work is owned work.** Concurrent work whose lifetime escapes its initiator is a resource with no enclosure — unreachable by cancellation, invisible to teardown, alive by accident.
- **Stages with different legal operations are different states.** Where a thing's life passes through phases that permit different acts, the phase is semantic and belongs in the representation (4 applied to lifecycle).
- **Endings deserve the care of beginnings.** Teardown in the wrong order, or not at all, violates the same enclosures that startup established; a system that knows how to stop is exhibiting the same principle as one that refuses to start wrong.

## 13. Quality is measured under counterfactual change

A system is not only its present behavior; it is its sensitivity to change. For each assumption *A* the system rests on, ask: when *A* changes, how much changes with it? Good architecture keeps `ΔSystem/ΔA` small for the assumptions that actually vary — a discrete sensitivity, honestly notated, not the derivative of a function no one has defined — which requires grouping elements by *shared reasons for change* and separating what must remain true from how it is currently achieved.

*Qualification:* insulation is bought with edges and indirection (principle 5), so it must be purchased only against changes with real probability mass. The sensitivity is weighted by the distribution of actual change — not by the space of imaginable change.

**Under it:**

- **Couple by shared reasons for change.** Things that change together belong together, whatever their superficial dissimilarity; things that change apart belong apart, whatever their resemblance — likeness of kind is not likeness of fate.
- **Sameness is sameness of reason, not of text.** Two fragments are one piece of knowledge only if they change for the same reason; unifying resemblances that share no fate buys a permanent edge to eliminate a repetition that was never a repetition of knowledge — and repetition of text, unlike repetition of knowledge, is a neutral fact awaiting evidence.
- **Separate stable meaning from unstable mechanism.** What must remain true and how it is currently achieved change at different rates; fused, the volatile drags the stable through every revision it undergoes.
- **Depend on what is required, not on what happens to be.** A dependency on the incidental inherits the incidental's rate of change; a dependency on the semantic inherits only the semantics' — usually far slower.
- **Change should exhaust itself near its source.** The distance a change propagates measures how thoroughly its assumption had leaked; in a well-factored system most changes die within the module that owns their reason.
- **Insure against probable change, not imaginable change.** Every insulation layer is a permanent, certain cost (an edge, an indirection) against a contingent benefit; bought where change is real it is architecture, bought everywhere it is superstition.
- **Design decisions are themselves framed facts.** The designer's knowledge of the domain grows over the system's life, so a commitment made early is made at the point of minimum knowledge (2 applied to the designer); while uncertainty is high, prefer assignments that are cheap to revise, and escalate structure on evidence rather than anticipation.
- **Compatibility is a promise about sensitivity.** A stable interface is a commitment that dependents' proofs survive the provider's evolution — the counterfactual principle turned outward, into a discipline about what may change and what may not.

## 14. Local checkability is the target all of this serves

The maintainer is a bounded prover (A1). A design is good precisely insofar as each important property can be verified from a context that fits within bounded attention — without opening the implementations of everything adjacent. When verifying a property requires the transitive closure of the system, the design has failed the axiom, whatever its other virtues.

The hierarchy deserves stating plainly. The ultimate objective is the frame itself: **minimize the lifetime cost of keeping the system's propositions true.** Local checkability is the primary architectural mechanism serving that objective — its dominant term, because verification under maintenance is where most of the cost accrues — but a mechanism nonetheless, and where the two ever diverge, the objective wins.

**Under it:**

- **Contracts must compose.** If a part guarantees `A ⇒ B` and its neighbor requires only `B`, the pair yields `A ⇒ C` from contracts alone — and a chain of parts can be trusted without opening any of them; where guarantees fail to compose, every whole must be re-proven from scratch.
- **Minimize simultaneously required context.** The burden of understanding grows with the facts that must be held at once *and* their interactions; a component resting on three independent assumptions is categorically easier than one resting on ten entangled ones.
- **What is needed to verify a thing should live near the thing.** Verification that requires a tour of the system pays a search cost before the proof cost; locality of evidence is half of local checkability.
- **An interface is the complete list of what may be relied upon.** If correct use requires knowledge the interface doesn't state, the interface is a partial truth — and its consumers' proofs rest partly on excavation (3 applied to contracts).
- **Modularity is proof-independence.** The honest definition: parts are modular exactly to the degree that each one's important properties can be established without reference to the others' interiors — everything else called modularity is topology.
- **Understandability is load-bearing.** By A1, a design too costly to verify will be maintained unverified; clarity is not a courtesy to the reader but a precondition of the system remaining correct under maintenance.

Every prior principle is a mechanism for this one: encoded facts shrink the premises; matched state spaces shrink the case analysis; sparse interaction and narrow authority shrink the interference to consider; explicit inputs make the premises enumerable; framed uncertainty bounds the unknown; translated failure keeps foreign mechanism out of local reasoning; algebraic operations remove ordering from the proof; declared consistency scopes remove joint states from it; enclosed lifetimes remove time from it; low change-sensitivity keeps yesterday's proofs valid tomorrow.

---

## Where the principles collide

The principles are not harmonious; real design is the adjudication of their conflicts, and a framework that pretends otherwise is a liturgy. The recurring collisions:

- **Encoding hardens (1 vs 13).** A fact paid into structure is cheap to consume and expensive to revise — the receipt itself acquires change-sensitivity. Encode where consumption is frequent and the rule stable; keep the volatile in data or policy, where revision doesn't refactor every signature that carries the type.
- **Today's variety vs tomorrow's (4 vs 13).** A representation matched exactly to today's meaningful situations resists the situation the domain invents next. The fit between representation and meaning is a target tracked over time, not achieved once.
- **Receipts vs surface (1 vs 5).** Emitting evidence of execution enlarges what can be observed, and the observable becomes depended upon. The resolution is a distinction, not a compromise: promised observations for a named audience versus incidental observability — maximize the first's usefulness, minimize the second's existence.
- **Resolve early vs commit late (8 vs 13).** Data-uncertainty should collapse at the perimeter, as early as possible; design-uncertainty should collapse as late as responsibility allows, because the designer's frame improves with time. These are opposite gradients for different unknowns, and confusing them produces either a defensive interior or a premature architecture.
- **Indivisibility vs liveness (11 vs 10).** Widening a consistency scope strengthens invariants and serializes the world; every fact added to the scope is availability spent. The invariant must be worth its scope.
- **Single home vs performance (6 vs the world).** Redundant representations exist because one home is sometimes too slow or too far; the collision is resolved honestly only by pricing the coherence obligation into the decision rather than discovering it later.

No principle is absolute outside its conditions of applicability. The arbiter is the frame: compare total lifetime discharge cost under the *actual* distribution of use, change, failure, and uncertainty. When two principles collide, at least one of them is defending an obligation that is smaller than it looks — the work is finding which.

---

## The limits of the framework itself

A foundation that cannot state its own limits is ideology.

- **The quantities are judgments in notation's clothing.** Consumption counts, change probabilities, validity horizons, edge weights — none is measurable in advance. The formalism organizes judgment; it does not replace it, and treating the notation as computation is the framework committing principle 3's sin against itself.
- **Structure-currency is not free, and over-paying is the signature failure.** Every encoding is an artifact with its own change-sensitivity, every scope a tax, every receipt a thing to maintain. The constraint from the frame governs everything here: an obligation must exist before it is assigned, and a framework this generative will happily generate proofs no one needed.
- **Enforcement is bounded by the enforcer.** The propositions structure can hold are the weak ones — nonempty, in-range, this-not-that. The deep invariants of a domain still rest on the lower rungs of the ladder, and honesty about which rung holds which proposition is part of the design.
- **The scope is correctness economics, and nothing else.** The framework prices what it costs to keep a system true; it is silent on whether the system is worth building, fast enough, humane to operate, or good for the people it touches. Those questions dominate this one more often than engineers like to admit.
- **The framework is spatially biased by ancestry.** It descends from type-driven traditions and is strongest about structure; principles 10 and 11 patch its temporal blind spot, but a corpus drawn from operations or distributed systems would have produced a different tree with the inverse bias. The extraction is honest; it is not neutral.

---

## Compression

The fourteen reduce to **three conserved reductions and one direction of flow**.

**Reduce possibility.** Fewer representable-but-meaningless states (4), fewer distinctions living only in minds (3), fewer unmodeled joint states and halfway worlds (11), fewer futures in which a fact must be re-proven (1, 12).

**Reduce interaction.** Fewer edges, declared and observable (5); smaller authority intersections (6); no invisible participants in any contract (7).

**Reduce propagation.** Uncertainty resolved at the perimeter and not re-imported (8); failure traveling exactly as far as its meaning (9); change absorbed near its source (13); environmental disorder absorbed by algebra rather than transmitted (10); partial change contained within its scope (11).

**And one direction:** correctness migrates *toward construction* — as early, as structural, as machine-checked as the domain permits; uncertainty migrates *toward the perimeter* — as late, as explicit, as contained as reality demands. These are not two policies but two gradients of the same field: each fact should be established at the point of maximum knowledge and minimum cost, and preserved from there to every point of use — within its frame, and never past it.

---

## The tests

The operational payoff of a first-principles document is the questions it lets you ask of a design you have never seen before:

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

---

## The final statement

> **Design is the assignment of proof obligations. The best assignment discharges each obligation once, at the point of maximum knowledge, in the cheapest currency available — structure before record, record before memory — and issues a receipt that travels with the value to the edge of its validity frame, where the obligation is knowingly, explicitly, purchased again.**

Or, at aphorism length:

> **A solved problem should leave a residue in structure. The measure of an architecture is how little must ever be proven twice — and how honestly it knows where its proofs expire.**
