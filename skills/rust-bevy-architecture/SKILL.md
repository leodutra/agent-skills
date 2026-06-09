---
name: bevy-architecture
description: Architecture method for Bevy (Rust ECS) game projects, grounded in how Bevy 0.18+ actually works rather than forcing DDD/Clean Architecture onto an ECS. Use this skill whenever designing, scaffolding, structuring, refactoring, or reviewing any Bevy codebase; deciding where a system/component/resource should live; choosing between Messages, Observers, or direct mutation; modeling components and game state; setting up schedules, states, assets, config, saves, determinism, networking, or AI. Trigger it for questions like "how should I structure my Bevy game", "where does this system go", "is this Bevy code over-engineered", or any Bevy folder/module/plugin layout decision, even when the word "architecture" is not used.
---

# Bevy Architecture

Domain-first method for long-lived Bevy games. It assumes Bevy 0.18+, Rust, and ECS-first thinking. Folders express intent; **crates and dependency direction enforce it**.

Every rule carries its reason. A rule without a stated *why* gets misapplied. An absolute with no named exception is a defect in this skill.

## Normative keywords

- **MUST / MUST NOT** — non-negotiable; violating it is a defect.
- **SHOULD / SHOULD NOT** — strong default; deviate only with a stated reason matching a named exception.
- **MAY** — a real option, no default preference.
- **CANNOT** — enforced by the compiler, the ECS, or physics. Not a choice.

Do not invent exceptions to a SHOULD beyond those named here.

## North Star (priority order; higher wins on conflict)

1. **Simulation correctness** — illegal game states are hard to represent; the sim is reproducible where the design needs it.
2. **Comprehensibility** — a name tells you where its behavior lives.
3. **Changeability** — features can be added, tuned, removed without ripple.
4. **Agent navigability** — predictable paths, narrow public surfaces, colocated behavior.
5. **Performance** — exploited where measured, never pre-optimized. ECS gives locality and parallelism for free.

You MUST NOT optimize for: engine-independence, maximum abstraction, or speculative multiplayer/modding before it exists.

## ECS reality (read first)

1. One `World`, shared storage. Module privacy hides items, not component access. Real isolation = crate boundaries, not folders.
2. Data/behavior separation is already given: components = data, systems = behavior. You do not police it; you use it.
3. Cross-cutting components (`Transform`, `Health`) are unavoidable — they need an explicit owner (see Layout).
4. Decoupling is a trade: a Message swaps a compile-time dependency for a timing/ordering one. Choose it deliberately.

---

## 1. Layout

Top-level folders MUST be gameplay capabilities, never ECS layers.

```text
src/
├── app/        # composition root: plugins, schedules, states, error handler. No gameplay.
├── domain/     # cross-cutting GAME components + identities (the shared vocabulary)
├── shared/     # business-free utilities: math, rng, diagnostics helpers
├── movement/   # ── features ──
├── combat/
├── ai/
└── main.rs
```

- The ONLY non-feature top-level folders allowed are `app/`, `domain/`, `shared/`. Any root `components/`, `systems/`, or `resources/` folder is a defect — it scatters one feature across the tree.
- `shared/` MUST be business-free. `domain/` MUST be business but feature-neutral.
- `domain/` MUST be sub-grouped by capability from day one (`domain/combat/`, `domain/characters/`, `domain/economy/`, `domain/world/`). A flat `domain/` becomes a junk drawer every feature depends on.
- Inside a feature, group by sub-capability and colocate tests:
  ```text
  combat/
  ├── plugin.rs      # the feature's PUBLIC API
  ├── components.rs  # components private to combat
  ├── attack/{intent.rs, resolve.rs, tests.rs}
  └── damage/{apply.rs, tests.rs}
  ```

## 2. Plugin = public API

- Each feature MUST expose exactly one `Plugin` (`CombatPlugin`) that registers its systems, messages, events, observers, sets, resources.
- Other code MUST depend only on what `plugin.rs`/`mod.rs` re-exports. Reaching into `combat::damage::apply::internal` is a defect.

## 3. Dependencies

Allowed direction (arrows point at what is depended on):

```text
app → feature → domain → shared
```

- Features MAY depend on `domain/` and `shared/`.
- Features SHOULD NOT depend on each other directly. Cross-feature behavior MUST go through **Messages on `domain/`-owned types** — this keeps the graph pointing only at `domain`/`shared`, prevents feature⇄feature spaghetti, and breaks cycles by construction.
- Exception: a feature MAY read another feature's public **component/message types** only when those types live in `domain/` (so the dependency is on `domain`, not the feature).
- The dependency graph MUST be acyclic and MUST NOT point "upward". Enforce with a fitness check (§17).

## 4. Crate split (on a trigger, not day one)

- Start single-crate. Promote a boundary to a crate only when it needs policing.
- The decisive trigger is the **sim/presentation split**: extract a `sim` crate so game logic CANNOT link `bevy_render`.
- Use Bevy 0.18 `2d_api`/`3d_api` feature collections: they give Bevy's API without the renderer, making the wall a compile error, not a hope.

---

## 5. Components, entities, resources

- **Component** = per-entity data. **Entity** = a thing in the world. **Resource** = single global instance.
- The player/enemies/projectiles MUST be entities, never resources. A resource MAY hold their `Entity` id (`PlayerEntity(Entity)`), not their state.
- A type MUST be a resource only if two could never exist; otherwise it is an entity.
- Use `#[require(...)]` to make illegal entities hard to spawn. Keep `require` graphs shallow and acyclic — cycles panic at startup.
- Prefer small **marker components** (`Enemy`, `Hostile`) over boolean fields when the marker drives query filtering. Use Bevy's `Disabled` to exclude entities, not custom `is_active` flags.

## 6. Type-driven modeling (from day one, not an escalation)

- Identities MUST be newtypes, not bare primitives — the compiler catches "wrong `u32` passed".
- Rule-bearing values SHOULD be value objects that make illegal states unrepresentable and own their **pure, local** invariants.
- Pure, World-free methods (`is_dead()`, `apply_damage(&mut self, n)`) MUST live on the type. Re-deriving `current <= max` in every system is the real anti-pattern.
- What MUST NOT live on a component: anything needing `World`, queries, spawn/despawn, sending messages, or cross-entity coordination. The line is **World access**, not "any method".

```rust
#[derive(Component, Clone, Copy)]
pub struct Health { current: u32, max: u32 }
impl Health {
    pub fn new(max: u32) -> Self { Self { current: max, max } } // invalid Health CANNOT be built
    pub fn is_dead(&self) -> bool { self.current == 0 }          // pure, local → belongs here
    pub fn apply_damage(&mut self, n: u32) { self.current = self.current.saturating_sub(n); }
}
```

- Model exclusive states as typed unions (`Holstered | Drawing | Ready | Firing`), not contradictory booleans.

## 7. Functional core, imperative shell

- Game decisions SHOULD be pure free functions taking plain data, returning plain data. The system is a thin shell: read queries → call core → write results.
- Why: the core is trivially unit/property-testable and deterministic; the shell is what headless sim tests exercise.

---

## 8. Communication: Messages vs Observers vs direct

| Tool | Bevy concept | Timing | Ordering | Use for |
|---|---|---|---|---|
| Direct write | system mutates components | this frame | by schedule | same feature, immediate invariant |
| **Message** | `Message` + `MessageWriter/Reader` | next time reader runs | by your schedule | cross-feature facts, fan-out, determinism-friendly |
| **Observer** | `Event` + `Observer`/`On<E>` | immediate | CANNOT be ordered | entity-lifecycle reactions, targeted hooks, propagation |

Decision rule:

- Same feature, immediate → **direct mutation**. Do not message yourself.
- Another feature reacts, next-tick consistency is fine → **Message** (the default cross-feature channel).
- Immediate, entity-targeted reaction needed → **Observer**. If reaction order matters, use Messages and order the reader systems — observers CANNOT be ordered.

Naming:

- Messages and Events MUST be past-tense facts (`DamageApplied`, `EnemyKilled`). Never vague mutations (`EntityUpdated`).
- Intent/request types SHOULD be suffixed `Intent`/`Request` (`AttackIntent`). They MUST NOT be suffixed `Command` — `Command` is reserved for Bevy's `Commands` queue.

Canonical flow: `Input → Intent (Message) → sim systems → Fact (Message) → presentation`. Observers are a side-channel, not the spine.

## 9. Scheduling, SystemSets, determinism

Schedule split:

- Gameplay simulation (physics, combat, movement, AI, economy) MUST run in `FixedUpdate`.
- Frame-rate work (input sampling, UI, camera, presentation, animation) runs in `Update`.
- `Startup` is for one-time init only.

**SystemSet convention (every feature follows the same shape — AI-friendly and orderable):**

```rust
#[derive(SystemSet, Clone, PartialEq, Eq, Hash, Debug)]
pub enum CombatSet { Intake, Resolve, Apply, EmitFacts }
```

- Each feature MUST define one such pipeline enum and assign its systems to a phase. Order phases with `.chain()`.
- Why: uniform phases make ordering explicit, cross-feature ordering legible, and the layout predictable.

**Fixed timestep is NOT determinism.** If the design needs reproducibility, declare a tier in an ADR:

- **T0** — none needed.
- **T1** (single-machine replay/test): order systems via SystemSets; enable schedule **ambiguity detection** in CI; thread one **seeded RNG** resource (no global RNG in sim); do not rely on incidental iteration order or randomly-seeded hash maps.
- **T2** (cross-machine lockstep): all of T1 **plus** floating-point determinism (fixed-point or `libm` path). Adopt only for lockstep netcode.

Most projects need T1 at most.

**Input→FixedUpdate seam:** input is sampled at frame rate, consumed at fixed rate. You MUST buffer input in `Update` into `Intent` messages that `FixedUpdate` drains — raw per-frame input dropped/double-counts.

Gate systems with `run_if` run conditions, not early `return` — the condition is visible to the scheduler.

## 10. States

- Use `States` for major modes (`Loading | MainMenu | Playing | GameOver`).
- Use `SubStates` for modes that exist only under a parent (e.g. `Paused` under `Playing`) — removed automatically when the parent leaves.
- Use `ComputedStates` for derived read-only views, to avoid duplicating "are we roughly here" checks.
- Attach `StateScoped` (or `#[states(scoped_entities)]`) so mode entities despawn on exit.
- You SHOULD NOT explode into tiny state flags. If a distinction gates one system, use a marker or run condition.

## 11. Layers

Direction MUST be one-way:

```text
infrastructure → simulation → presentation
```

- Presentation MAY read simulation via `Changed<T>` and fact Messages. Simulation MUST NOT read presentation components or assets.
- Enforce with the `sim` crate split (§4): then "sim reads a sprite" is a compile error.
- Input is presentation-adjacent; it produces `Intent` and lives in `Update`, never in sim logic.

---

## 12. Assets

- Load handles once at startup/loading and store them in **typed per-feature resources**. Systems read the resource.
- You MUST NOT call `asset_server.load(...)` ad hoc inside gameplay systems — scattered handles cause duplicate loads and untracked readiness.

```rust
#[derive(Resource)]
pub struct CombatAssets { pub hit_sound: Handle<AudioSource> }
```

## 13. Config

- Config files (RON/TOML) MUST be deserialized once at the edge into typed domain structs.
- Simulation MUST consume typed config (`EnemyStats`, `WeaponConfig`), never file formats — same parse-don't-validate boundary as §6.

## 14. Persistence / saves

- Principle: decouple the persistence schema from the runtime layout. It is NOT "never serialize the `World`".
- Player progression SHOULD use hand-authored, **versioned** `SaveGame` structs with explicit migration.
- Levels/prefabs/editor data MAY use reflection scenes (`DynamicScene`) with registered types.
- Persisted types are a public contract: changing one requires a version bump + migration, never a silent field edit.

## 15. Networking

- Authority MUST be server-side; client state is never trusted. Clients send input/intent, run prediction + presentation.
- Pick the model in an ADR — it sets the determinism tier: **state replication** (forgiving, T1, more bandwidth) vs **lockstep** (cheap bandwidth, requires T2).
- Do not build networking abstractions before a model is chosen.

## 16. AI

- There is no quality ranking among techniques. Choose by problem shape:
  - **Behavior Trees** — authored, inspectable, sequenced behavior.
  - **Utility AI** — many agents picking among options with smooth tradeoffs; weak at long sequences.
  - **GOAP** — agent plans its own action sequence; powerful, harder to debug/scale.
- A project MAY mix them. The AI feature consumes facts and emits `Intent` like any feature — it MUST NOT be a privileged subsystem reaching across boundaries.

---

## 17. Errors, assertions, observability

**Errors**

- Systems/observers SHOULD return `Result<(), BevyError>` and use `?` for should-never-fail accesses (`query.single()?`).
- Develop with the panicking handler; ship with a logging handler (`set_error_handler`).
- Expected absence (no target this frame) is control flow (`let Ok(x) = .. else { return Ok(()) }`), not an `Err`.

**Assertions / invariants**

- Invariants that the type system CANNOT express SHOULD be enforced with `debug_assert!` in the sim path (zero release cost), and with `assert!` for setup/config validation that must hold in release.

```rust
debug_assert!(health.current <= health.max);
assert!(total_weight > 0.0, "loot table must have positive weight");
```

**Observability** (first-class, not an afterthought — large games are undebuggable without it)

- Hot systems and core decision functions SHOULD carry tracing spans: `#[tracing::instrument(skip_all)]`.
- Key facts SHOULD emit structured logs: `info!(attacker = ?e, damage = n, "attack resolved")`.
- Each feature SHOULD expose diagnostics/metrics from the start; performance problems found late are expensive.

## 18. Testing

- **Functional-core unit tests** — pure decision fns; no Bevy, instant; most logic coverage lives here.
- **Headless sim tests** — build an `App`, add the plugin, insert inputs, `app.update()` N times, assert on components/resources/messages. The backbone of gameplay testing.
- **Property tests** — for combat/economy/crafting/loot invariants, run against the core.
- Tests MUST colocate with the code they cover; only cross-feature behavior goes in a top-level `tests/`.

## 19. Governance

- Encode load-bearing rules as **fitness functions** (CI), so the architecture polices itself:
  - dependency direction is acyclic and never upward (§3);
  - the `sim` crate's tree contains no `bevy_render` (§11);
  - schedule ambiguity gate for sim schedules (§9, T1);
  - spawning each archetype does not panic (catches `require` cycles).
- Record each considerable decision as an **ADR**; mark superseded ones, never delete. Seed ADRs for: determinism tier, networking model, persistence strategy, any feature promoted to a crate.
- Maintain `ARCHITECTURE.md` and `AGENTS.md` pointing tools at the layout and these rules.

## 20. Evolution path (earn every abstraction)

Stay at the earliest stage that meets current needs; advance only on a concrete trigger.

1. **Foundation** — single crate; feature folders; `domain/` + `shared/`; newtypes + typed components; FixedUpdate/Update split; SystemSet pipelines; states. *Most prototypes stay here.*
2. **Determinism (T1)** — SystemSet ordering, ambiguity gate, seeded RNG when replays/tests/balance need reproducibility.
3. **Crate split** — extract `sim` (no `bevy_render`) when the layer wall must be compiler-enforced or build/ownership demands it.
4. **Enforcement** — add fitness functions when boundaries drift under churn.
5. **Networking / lockstep (T2)** — deterministic FP + netcode model only when multiplayer is committed.

Flag over-engineering (a `sim` crate for a jam game; lockstep FP with no multiplayer) as readily as under-engineering. When unsure, pick the lower stage and name the trigger that would justify advancing.

---

## Review checklist (when reviewing a Bevy codebase)

1. **Layout** — top-level folders are capabilities? Only `app`/`domain`/`shared` are non-features? `domain/` sub-grouped, not a junk drawer?
2. **Dependencies** — acyclic, never upward? Features talk via Messages on domain types, not direct feature→feature deps? Plugin is the only public surface?
3. **Types** — identities are newtypes? Rule-bearing values are value objects with pure local methods? Illegal states unrepresentable? No World access on components?
4. **Communication** — Messages for facts, Observers for immediate reactions, direct for same-feature? Facts past-tense? No `Command` suffix collision?
5. **Scheduling** — sim in `FixedUpdate`? Uniform SystemSet pipeline per feature? Determinism tier declared and its requirements met? Input buffered across the seam?
6. **Layers** — one-way infra→sim→presentation? Enforced by crate split where claimed?
7. **Assets/config** — handles in typed resources (no ad-hoc loads)? Config parsed once at the edge into typed structs?
8. **Robustness** — `Result`/`?` in fallible systems? `debug_assert!` for non-type invariants? Spans + structured logs on hot paths and key facts?
9. **Governance** — fitness functions enforce the rules? ADRs for the dominating decisions? Tests colocated, core unit-tested, sim tested headlessly?
10. **Restraint** — any abstraction that has not earned its place? Could it use fewer concepts?
