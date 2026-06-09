---
name: rust-wgpu-functional
description: >
  Idiomatic Rust skill for wgpu, bare-metal GPU programming, game engines, renderers,
  and high-performance systems code. Applies functional programming principles — purity,
  composition, algebraic types, zero-cost abstractions — while never sacrificing runtime
  performance. Use this skill whenever the user asks to write Rust code involving wgpu,
  GPU pipelines, render passes, compute shaders, ECS, game loops, real-time systems,
  bare-metal performance code, or any Rust project where performance is a hard constraint.
  Also trigger when the user asks for Rust code reviews, refactors, or architecture
  advice where functional idioms and performance must coexist. Trigger even when the
  user doesn't explicitly mention "functional" — if they paste Rust code that touches
  wgpu::Device, wgpu::Queue, wgpu::CommandEncoder, or any GPU resource type, use this
  skill. Trigger on mentions of: wgpu, winit, WGSL, render pipeline, compute pipeline,
  bind group, GPU buffer, ECS, bevy (low-level), bare-metal Rust, zero-copy, SIMD,
  cache-friendly, data-oriented design, game engine, renderer, frame loop, shader,
  vertex buffer, index buffer, texture, sampler, depth buffer, compute dispatch,
  particle system, scene graph, frustum culling, instanced rendering, indirect draw,
  GPU profiling, or any Rust performance-critical system. Also trigger when the user
  asks to "make this faster", "reduce allocations", "optimize this Rust", "review my
  Rust code", or pastes Rust code with clone(), unwrap(), Box<dyn>, or Vec allocations
  in hot paths that could benefit from functional refactoring.
---

# Rust · wgpu · Functional Performance Engineering

This skill produces idiomatic Rust code that is **functionally composed, performance-first,
and maintainable at scale**. Every decision follows one meta-principle:

> **Make the implicit explicit. Make the illegal impossible. Make the fast path the only path.**

## Core Philosophy

Performance and clean architecture are not in tension — they compound. Splitting code into
small pure functions enables inlining, monomorphization, and branch elimination. Algebraic
types with exhaustive matching eliminate runtime checks. Immutability enables fearless
concurrency. The compiler rewards functional discipline with faster binaries.

**When in doubt:** prefer the approach that gives the compiler more information at compile
time and less work at runtime.

## Decision Framework

Before writing any code, evaluate along these axes:

1. **Hot path or cold path?** Hot paths get inlined, unrolled, cache-optimized. Cold paths
   get clarity and modularity. Never optimize cold paths at the expense of readability.
2. **Compile-time or runtime?** Push every decision possible to compile time — generics,
   const, type-state patterns. Runtime dynamism (dyn Trait, HashMap lookups) only when
   the domain genuinely requires it.
3. **Owned or borrowed?** Default to borrowing. Own only at boundaries (async tasks,
   thread spawns, storage). Never clone to satisfy the borrow checker — restructure instead.
4. **Allocation budget?** Every `Vec::new()`, `Box`, `String` is a decision. Pre-allocate,
   reuse, pool. Arena allocators for frame-scoped data.
5. **Measured or assumed?** Distinguish "removes known work" from "measured faster".
    Structural wins can be reasoned about. Runtime wins must be timed, especially when work
    shifts across passes rather than disappearing.

## Architecture Rules

### Functional Core, Imperative Shell

Structure every system as:

```
[ Pure logic ]  →  produces descriptions of work
[ Thin shell ]  →  executes side effects (GPU commands, I/O, allocation)
```

The pure core is testable without a GPU. The shell is a thin translation layer.
This is not optional — it is the primary architectural invariant.

For hot paths, prefer caller-provided outputs over fresh allocations:

```rust
fn collect_draw_calls(scene: &Scene, camera: &Camera, out: &mut Vec<DrawCall>) {
    out.clear();
    out.extend(scene.visible_entities(camera).map(DrawCall::from_entity));
}
```

Returning a new `Vec` is acceptable on cold paths. Repeated frame-time allocation is not.

**Example — Render pipeline:**
```rust
// PURE: describes what to draw (no GPU types)
fn plan_draw_calls(scene: &Scene, camera: &Camera) -> Vec<DrawCall> { ... }

// SHELL: translates to GPU commands (side-effectful, thin)
fn execute_draw_calls(
    encoder: &mut wgpu::CommandEncoder,
    calls: &[DrawCall],
    resources: &GpuResources,
) { ... }
```

### Separation of Concerns via Composition

Each module owns exactly one responsibility. Compose via function arguments
and return values, never via shared mutable state.

```
input → parse → validate → transform → describe_effects → execute
```

Every arrow is a pure function except the last. If a function both computes
and side-effects, split it.

### Small Functions, Big Inlining

Functions of 3–10 lines are the sweet spot. The compiler inlines aggressively
when functions are small and generic. This means small functions are often
*faster* than large monolithic ones — the optimizer sees through them.

Mark hot-path helpers `#[inline]` or `#[inline(always)]` only after profiling
confirms a cross-crate boundary blocks inlining. Within a crate, trust LLVM.

## Idiomatic Patterns

Read `references/patterns.md` for detailed code patterns covering:
- Type-state pattern for compile-time pipeline validation
- Zero-cost iterator pipelines vs manual loops
- Algebraic error handling (no panics in library code)
- Arena allocation and frame-scoped temporaries
- SoA (Struct of Arrays) for cache-friendly GPU data
- Newtype pattern for unit safety (WorldPos vs ScreenPos)
- Builder pattern for complex GPU resource creation

Read `references/wgpu-idioms.md` for wgpu-specific patterns covering:
- Bind group layout composition
- Render pass and compute pass structure
- Host/shader contract review
- Buffer management and staging patterns
- Pipeline caching and lazy initialization
- WGSL shader module organization
- Surface configuration and resize handling

Read `references/perf-checklist.md` before finalizing any code for:
- Allocation audit
- Cache-line analysis
- Branch elimination opportunities
- Parallelism and async considerations

Read `references/examples.md` for full before/after refactoring walkthroughs.
Use these as templates when reviewing or restructuring user code.

## Scripts

Run `.github/skills/rust-wgpu-functional/scripts/generate_layout_tests.py` to auto-generate memory layout tests.
Annotate structs with `/// @layout size=32 align=4` (or `cache_line_fit`,
`gpu_aligned`) and the script produces `#[cfg(test)]` assertions for size,
alignment, and field offsets. Run it after any struct change to catch silent
layout regressions.

```bash
python .github/skills/rust-wgpu-functional/scripts/generate_layout_tests.py src/types.rs > src/types_layout_tests.rs
python .github/skills/rust-wgpu-functional/scripts/generate_layout_tests.py src/ --recursive > tests/layout_tests.rs
```

Layout tests are necessary but not sufficient for Rust/WGSL interop. Also verify:
- Rust `BindGroupLayoutEntry` visibility and read/write mode matches WGSL declarations
- Rust bind group entries target the same binding indices as the shader
- one pass owns each read-write aggregate output such as indirect args or scan totals
- Rust dispatch sizing agrees with shader-side bounds guards and scan hierarchy limits

Treat the pipeline layout, bind group entries, and WGSL `@group/@binding` declarations as
one contract and review them together.

## GPU Contract Rules

### Host/Shader ABI Is a Single Unit

For any buffer shared with WGSL:
- use `#[repr(C)]` and `bytemuck::Pod + Zeroable` on Rust structs
- keep field order identical between Rust and WGSL
- validate size and alignment after every structural change
- prefer explicit padding fields over implicit layout assumptions

If a struct exists only in WGSL but controls Rust behavior, such as an indirect-draw struct,
document its byte layout next to the Rust buffer creation code.

### Bindings Must Be Reviewed as a Triple

Every binding change must keep WGSL `@group/@binding`, Rust `BindGroupLayoutEntry`, and Rust
`BindGroupEntry` aligned. See `references/wgpu-idioms.md` §4 for the full review checklist.

### Multi-Pass Compute Needs Explicit Ownership

In culling, scan, compaction, and indirect-draw pipelines:
- each pass should own exactly one transformation of data
- one pass writes each aggregate output; later passes only consume it
- encode scan hierarchy limits as Rust assertions near buffer sizing and dispatch math
- prefer local recomputation over oversized intermediate buffers when it reduces bandwidth

### WGSL Safety Rules

- Every compute shader must guard storage-buffer indexing with runtime bounds checks.
- `arrayLength()` is for bounds and derived limits, not wishful assumptions about allocations.
- Prefix scans require the full read-barrier-write-barrier sequence at every step.
- Avoid atomics when staged scan/compaction removes global contention at scale.

## Profiling and Verification

Optimize by proof, not by narrative.

- Separate CPU planning, compute, draw, and composite timings.
- Timestamp writes must bracket actual work, not placeholders.
- Compare before/after at fixed camera states and fixed quality settings.
- If a change removes duplicated shader math, that is a structural win.
- If a change adds passes, treat it as unproven until timings show the tradeoff is favorable.
- State uncertainty plainly when measurement is still missing.

See `references/perf-checklist.md` §5 for GPU-specific verification steps.

## Type System as Performance Tool

### Algebraic Data Types — Model the Domain Exactly

```rust
// The GPU pipeline has exactly these states. No invalid transitions possible.
enum PipelineState {
    Uninitialized,
    Compiling { shader_source: ShaderSource },
    Ready { pipeline: wgpu::RenderPipeline },
    Error { reason: PipelineError },
}
```

Match exhaustively. Never use `_ =>` wildcard on domain enums — you *want*
the compiler to break your code when you add a variant.

### Generics Over Dynamic Dispatch

```rust
// YES — monomorphized, zero-cost, inlined
fn process_vertices<V: Vertex>(vertices: &[V]) -> BoundingBox { ... }

// AVOID on hot paths — vtable indirection, no inlining
fn process_vertices(vertices: &[dyn Vertex]) -> BoundingBox { ... }
```

Use `dyn Trait` only for heterogeneous collections on cold paths (plugin
systems, configuration, error handling).

### Const Generics for Compile-Time Dimensions

```rust
struct Matrix<const ROWS: usize, const COLS: usize> {
    data: [[f32; COLS]; ROWS],
}

// Multiplication is only valid when dimensions align — compile-time checked
impl<const M: usize, const N: usize, const P: usize>
    std::ops::Mul<Matrix<N, P>> for Matrix<M, N>
{
    type Output = Matrix<M, P>;
    fn mul(self, rhs: Matrix<N, P>) -> Matrix<M, P> { ... }
}
```

## Iterator Pipelines — Declarative and Fast

Rust iterators often compile to the same code as hand-written loops. Prefer them
when they preserve clarity and let LLVM fuse the work. Switch to explicit loops when
the iterator form obscures data movement, blocks output reuse, or prevents obvious
vectorization.

```rust
// Declarative, fused, zero-allocation, auto-vectorizable
let visible: Vec<DrawCall> = entities.iter()
    .filter(|e| frustum.contains(e.bounds()))
    .sorted_unstable_by_key(|e| e.material_id()) // requires itertools::Itertools
    .map(|e| e.to_draw_call(camera))
    .collect();
```

When iterators cannot express the pattern (e.g., parallel mutation of
disjoint slices), drop to `split_at_mut` or `chunks_exact_mut` — never
to raw indexing with bounds checks disabled.

## Error Handling — Total Functions, No Panics

```rust
// Every function in library code returns Result or is infallible.
// Panics are reserved for: tests, main(), and proven-unreachable invariants.

// Domain errors are algebraic — not stringly typed
#[derive(Debug, thiserror::Error)]
enum ShaderError {
    #[error("compilation failed: {diagnostic}")]
    Compilation { diagnostic: String, line: u32 },
    #[error("unsupported feature: {feature}")]
    Unsupported { feature: &'static str },
}

// The ? operator composes errors through pure function chains
fn load_pipeline(device: &wgpu::Device, source: &str) -> Result<Pipeline, ShaderError> {
    let module = compile_shader(source)?;
    let layout = derive_layout(&module)?;
    Ok(build_pipeline(device, &module, &layout))
}
```

## Code Generation Checklist

When generating Rust code with this skill, verify every output against:

1. **No unnecessary allocations** — Can this Vec be an iterator? Can this String be &str?
2. **No clone() without justification** — Each clone gets a `// clone: <reason>` comment
3. **No unwrap() in non-test code** — Use `?`, `map`, `and_then`, or `unwrap_or`
4. **Exhaustive matching** — No `_ =>` on domain enums
5. **Pure functions dominate** — Side effects only at boundaries
6. **Types encode invariants** — If it compiles, it's valid
7. **Iterators over indexing** — Unless disjoint mutation requires slices
8. **Borrowing over owning** — Own only at async/thread/storage boundaries
9. **Generics over dyn** — On hot paths, always monomorphize
10. **Const over let** — If it's known at compile time, make it const
11. **Rust/WGSL contract verified** — Layouts, bindings, visibility, and read/write modes match
12. **Optimization claim is evidenced** — structural proof or timing data, clearly labeled

## Naming Conventions

- Types: `PascalCase`, descriptive noun — `VertexBuffer`, `RenderPassDescriptor`
- Functions: `snake_case`, verb-first — `build_pipeline`, `compute_normals`
- Pure functions returning bool: `is_` or `has_` prefix — `is_visible`, `has_transparency`
- Constructors: `new`, `with_capacity`, `from_*`
- Conversions: `to_*` (owned), `as_*` (borrowed), `into_*` (consuming)
- Unsafe wrappers: `*_unchecked` — and always document the safety invariant

## Refactoring Examples

Read `references/examples.md` for full before/after transformations showing:
- OOP entity hierarchy → data-oriented SoA with pure systems
- Monolithic render function → functional core / imperative shell split
- Runtime type checks → type-state compile-time enforcement
- Scattered allocations → arena-scoped frame temporaries
- Stringly-typed errors → algebraic domain errors with monadic chaining

Each example shows the original code, explains what's wrong, and walks
through the refactored version with performance annotations.

## When NOT to Apply Functional Purity

Some patterns legitimately require mutation. Don't fight these — contain them:

- **ECS update loops** — Mutate components in-place, but keep system functions pure
  in their *logic* (take input components, produce output components).
- **GPU buffer writes** — `queue.write_buffer` is inherently side-effectful.
  Prepare the data purely, execute the write in the shell.
- **Frame allocators / arenas** — Bump allocation is mutable by nature. Wrap it,
  expose an immutable borrowing API, reset at frame boundaries.
- **Hot inner loops** — If a profiler shows that an iterator chain prevents
  auto-vectorization in a specific case, drop to a `for` loop with raw slice
  access. Comment why. This should be rare (<5% of code).
