# Performance Checklist

Run through this checklist before finalizing any performance-critical code.
Each section has a "check" (what to look for) and a "fix" (what to do).

---

## 1. Allocation Audit

**Check:** Search for every `Vec::new()`, `String::new()`, `Box::new()`,
`HashMap::new()`, `.to_string()`, `.to_owned()`, `.clone()`, `format!()`.

**Fix:**
- Replace `Vec::new()` + push loop → `Vec::with_capacity(n)` or iterator `.collect()`
- Replace per-frame `Vec::new()` → reuse a `Vec` via `.clear()` + `.extend()`
- Replace `String` with `&str` when the string doesn't need ownership
- Replace `Box<dyn Trait>` on hot paths with enum dispatch or generics
- Replace `HashMap` on small fixed sets with arrays, perfect hashing, or `match`
- Replace `format!()` in hot paths with stack-allocated formatting (`itoa`, `ryu`, `arrayvec`)
- Every remaining `.clone()` gets a `// clone: <reason>` comment

**Target:** Zero allocations in the render loop. All allocations happen
during initialization or use pre-allocated pools.

---

## 2. Cache-Line Analysis

**Check:** For data structures iterated in hot loops, calculate:
- Struct size (`std::mem::size_of::<T>()`)
- Fields accessed per iteration
- Bytes touched vs bytes loaded per cache line (64 bytes on x86)

**Fix:**
- If accessing <50% of struct fields in a loop → SoA layout (see patterns.md §4)
- If struct is >64 bytes and fully accessed → consider splitting hot/cold fields
- Align frequently accessed data to cache line boundaries:
  ```rust
  #[repr(C, align(64))]
  struct CacheAligned<T>(T);
  ```
- Sort arrays by access pattern (e.g., depth-sort for front-to-back rendering)
- Prefer `Vec<T>` over `LinkedList<T>` — always. Linked lists are cache poison.

**Hot/cold field split example:**
```rust
// BEFORE: 96 bytes, but culling only needs bounding_sphere (16 bytes)
struct Entity {
    bounding_sphere: BoundingSphere,  // hot — used in frustum culling
    transform: Mat4,                   // hot — used in rendering
    name: String,                      // cold — used in debug UI
    metadata: EntityMetadata,          // cold — used in serialization
}

// AFTER: hot data is contiguous, cold data is indirected
struct EntityHot {
    bounding_sphere: BoundingSphere,
    transform: Mat4,
}

struct EntityCold {
    name: String,
    metadata: EntityMetadata,
}

struct EntityStore {
    hot: Vec<EntityHot>,    // iterated every frame — tight, cache-friendly
    cold: Vec<EntityCold>,  // accessed by index only when needed
}
```

---

## 3. Branch Elimination

**Check:** Look for branches in inner loops — `if`, `match`, `?` on hot paths.

**Fix:**
- Sort input data to make branches predictable (all trues, then all falses)
- Replace `if` with branchless arithmetic where possible:
  ```rust
  // Branchy
  let result = if condition { a } else { b };

  // Branchless (when a and b are cheap to compute)
  let mask = condition as u32;
  let result = a * mask + b * (1 - mask);
  ```
- Hoist loop-invariant branches outside the loop:
  ```rust
  // BEFORE: branch evaluated N times
  for item in items {
      if config.use_hdr { process_hdr(item); }
      else { process_sdr(item); }
  }

  // AFTER: branch evaluated once
  let processor: fn(&Item) = if config.use_hdr { process_hdr } else { process_sdr };
  for item in items {
      processor(item);
  }
  ```
- Use enum dispatch instead of trait objects on hot paths (static dispatch
  eliminates the vtable branch)

---

## 4. SIMD and Auto-Vectorization

**Check:** Verify that tight numerical loops auto-vectorize.
Use `cargo asm` or `godbolt.org` to inspect the output.

**Fix — help the compiler vectorize:**
- Use `chunks_exact()` instead of `chunks()` (the remainder handling in
  `chunks()` can prevent vectorization)
- Ensure loop bodies have no function calls that aren't `#[inline]`
- Avoid early returns or breaks in inner loops
- Use `unsafe { slice.get_unchecked(i) }` only after proving bounds
  (prefer iterators which already skip bounds checks)
- Use aligned data: `#[repr(C, align(16))]` for SIMD-width structs
- For explicit SIMD, use `std::simd` (nightly) or `glam` for math types
  which auto-select SIMD backends

**Example — helping auto-vectorization:**
```rust
// This auto-vectorizes because:
// 1. chunks_exact gives the compiler a known stride
// 2. No branches in the body
// 3. All operations are data-parallel
fn apply_transform(positions: &mut [[f32; 4]], matrix: &[[f32; 4]; 4]) {
    for pos in positions.iter_mut() {
        let x = pos[0];
        let y = pos[1];
        let z = pos[2];
        let w = pos[3];
        pos[0] = matrix[0][0] * x + matrix[1][0] * y + matrix[2][0] * z + matrix[3][0] * w;
        pos[1] = matrix[0][1] * x + matrix[1][1] * y + matrix[2][1] * z + matrix[3][1] * w;
        pos[2] = matrix[0][2] * x + matrix[1][2] * y + matrix[2][2] * z + matrix[3][2] * w;
        pos[3] = matrix[0][3] * x + matrix[1][3] * y + matrix[2][3] * z + matrix[3][3] * w;
    }
}
```

---

## 5. GPU-Specific Performance

**Check:**
- How many draw calls per frame? (target: <1000 for desktop, <200 for mobile)
- How many bind group changes? (most expensive state change)
- How many buffer uploads per frame?
- What's the GPU buffer alignment? (`device.limits().min_uniform_buffer_offset_alignment`)

**Fix:**
- Batch draw calls by material/pipeline (sort by bind group to minimize switches)
- Use instanced drawing for repeated geometry
- Use dynamic offsets in uniform bind groups for per-object data instead of
  separate bind groups
- Use a single large vertex/index buffer with offsets (buffer atlas)
- Use indirect drawing (`draw_indirect`, `draw_indexed_indirect`) for
  GPU-driven rendering
- Pack small uniforms into a single buffer with offsets aligned to
  `min_uniform_buffer_offset_alignment`

**Verification:**
- Measure compute, draw, and composite passes separately before claiming a GPU win
- Prefer fixed camera bookmarks or deterministic scenes for before/after comparisons
- If a change adds passes, verify reduced contention or shader work outweighs dispatch overhead
- Treat timestamp ranges that do not wrap actual work as invalid data, not rough estimates

**Bind group change minimization:**
```rust
fn sort_draw_calls_for_gpu(calls: &mut [DrawCall]) {
    // Primary sort: pipeline (most expensive change)
    // Secondary sort: bind group 1 / material
    // Tertiary sort: front-to-back for opaque, back-to-front for transparent
    calls.sort_unstable_by(|a, b| {
        a.pipeline_key.cmp(&b.pipeline_key)
            .then(a.material_key.cmp(&b.material_key))
            .then(a.depth.partial_cmp(&b.depth).unwrap_or(std::cmp::Ordering::Equal))
    });
}
```

---

## 6. Parallelism Audit

**Check:** Is CPU work being done single-threaded that could be parallel?

**Fix:**
- Use `rayon` for data-parallel CPU work:
  ```rust
  use rayon::prelude::*;

  // Frustum culling — embarrassingly parallel
  let visible: Vec<&Entity> = entities.par_iter()
      .filter(|e| frustum.contains(&e.bounding_sphere))
      .collect();
  ```
- Use `rayon` for parallel sort: `.par_sort_unstable_by()`
- Pipeline GPU work ahead: submit command buffers while CPU prepares the next frame
- Use double/triple buffering for uniform data to avoid GPU stalls

**Important:** Only parallelize when the workload justifies it. For <1000
items, single-threaded is usually faster due to thread overhead.

---

## 7. Async and I/O Performance

**Check:** Are there blocking calls on the render thread?

**Fix:**
- All file I/O, network, and asset loading goes on a separate thread/task
- Use channels (`crossbeam::channel` or `tokio::sync::mpsc`) to communicate
  results back to the render thread
- Asset loading pipeline:
  ```
  [IO thread: read bytes] → channel → [CPU thread: decode/process] → channel → [Render thread: upload to GPU]
  ```
- Never `pollster::block_on()` inside the event loop — use a dedicated async runtime
- For buffer readback (e.g., screenshots, GPU profiler data), use
  `buffer.slice(..).map_async()` and poll on a background task

---

## 8. Compile-Time Performance

**Check:** Are there computations happening at runtime that could be const?

**Fix:**
- Use `const fn` for anything computable at compile time
- Use `include_bytes!()` for embedded assets (shaders, textures)
- Use `phf` crate for compile-time perfect hash maps
- Use const generics to specialize hot functions:
  ```rust
  fn process_vertices<const HAS_NORMALS: bool>(data: &[u8]) {
      // The branch is eliminated at compile time — two monomorphized versions
      if HAS_NORMALS {
          // process with normals
      } else {
          // skip normal processing
      }
  }
  ```

---

## 9. Memory Layout Verification

Before shipping, verify struct layouts match your assumptions:

```rust
#[cfg(test)]
mod layout_tests {
    use super::*;
    use std::mem::{size_of, align_of};

    #[test]
    fn verify_vertex_layout() {
        assert_eq!(size_of::<Vertex>(), 32, "Vertex must be 32 bytes for GPU alignment");
        assert_eq!(align_of::<Vertex>(), 4, "Vertex must be 4-byte aligned");
    }

    #[test]
    fn verify_uniform_layout() {
        assert_eq!(
            size_of::<CameraUniforms>() % 16, 0,
            "Uniform buffer size must be 16-byte aligned for WebGPU"
        );
    }

    #[test]
    fn verify_cache_line_fit() {
        assert!(
            size_of::<EntityHot>() <= 64,
            "EntityHot should fit in a single cache line"
        );
    }
}
```

---

## 10. Profiling-First Rule

**Never optimize without data.** The checklist above identifies *candidates*.
Actual optimization requires measurement.

**Toolchain:**
- `cargo flamegraph` — CPU profiling
- `tracy` — frame-level profiling with GPU timeline
- `cargo asm` / godbolt.org — verify inlining and vectorization
- `perf stat` — cache miss rates, branch mispredictions
- RenderDoc / Nsight — GPU pipeline inspection
- `wgpu` timestamp queries — per-pass GPU timing

**Workflow:**
1. Profile first. Identify the bottleneck.
2. Check this list for applicable fixes.
3. Apply the fix.
4. Profile again. Verify improvement.
5. If no measurable improvement, revert.

Readable code that runs at 90% of theoretical max beats unreadable code
at 95%. Optimize the 10% of code that runs 90% of the time.
