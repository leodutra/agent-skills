# Refactoring Examples

Concrete before/after transformations. Each shows the original code,
what's wrong, and the refactored version with performance annotations.

## Table of Contents

1. OOP Entity → Data-Oriented SoA
2. Monolithic Render → Functional Core / Imperative Shell
3. Runtime Type Checks → Type-State
4. Scattered Allocations → Arena-Scoped
5. Stringly-Typed Errors → Algebraic Domain Errors

---

## 1. OOP Entity → Data-Oriented SoA

### Before — Object-Oriented Entity

```rust
struct Entity {
    position: Vec3,
    velocity: Vec3,
    mesh: Mesh,
    material: Material,
    health: f32,
    name: String,
    ai_state: AiState,
    bounding_box: Aabb,
    is_active: bool,
}

impl Entity {
    fn update(&mut self, dt: f32) {
        if !self.is_active { return; }
        self.position += self.velocity * dt;
        self.bounding_box = self.mesh.compute_aabb(self.position);
        self.ai_state.think(dt);
    }

    fn render(&self, encoder: &mut wgpu::CommandEncoder, camera: &Camera) {
        if !self.is_active { return; }
        if !camera.frustum().contains(&self.bounding_box) { return; }
        // 20 lines of GPU commands mixed with logic...
    }
}

// Game loop — iterates all entities, touches everything
fn update_world(entities: &mut Vec<Entity>, dt: f32) {
    for entity in entities.iter_mut() {
        entity.update(dt);
    }
}
```

**Problems:**
- Entity is 200+ bytes. Iterating for physics touches `position` and `velocity`
  (24 bytes) but loads the entire struct per cache line.
- `update()` mixes physics, AI, and spatial queries — can't parallelize.
- `render()` mixes culling logic with GPU commands — untestable without GPU.
- `is_active` branch in every function — branch predictor thrashes on mixed data.
- `name: String` forces heap allocation per entity even when never read at runtime.

### After — Data-Oriented SoA with Pure Systems

```rust
// Hot data — contiguous, cache-optimal per system
struct PhysicsData {
    positions: Vec<Vec3>,      // 12 bytes each, contiguous
    velocities: Vec<Vec3>,     // 12 bytes each, contiguous
}

struct SpatialData {
    bounding_boxes: Vec<Aabb>,
}

struct RenderData {
    mesh_ids: Vec<MeshId>,     // handle, not owned — 4 bytes
    material_ids: Vec<MaterialId>,
}

// Cold data — accessed rarely, indirected by index
struct MetaData {
    names: Vec<String>,
    ai_states: Vec<AiState>,
    health: Vec<f32>,
}

// Active entities tracked as a bitset — no per-entity branch
struct ActiveSet(Vec<u64>);  // 1 bit per entity, 64 entities per cache line

impl ActiveSet {
    fn is_active(&self, index: usize) -> bool {
        self.0[index / 64] & (1 << (index % 64)) != 0
    }

    fn active_indices(&self) -> impl Iterator<Item = usize> + '_ {
        self.0.iter().enumerate().flat_map(|(word_idx, &bits)| {
            (0..64).filter(move |bit| bits & (1 << bit) != 0)
                   .map(move |bit| word_idx * 64 + bit)
        })
    }
}

// PURE SYSTEM: physics — touches only positions + velocities
fn update_physics(physics: &mut PhysicsData, active: &ActiveSet, dt: f32) {
    for i in active.active_indices() {
        // Two contiguous arrays, sequential access, auto-vectorizable
        physics.positions[i] += physics.velocities[i] * dt;
    }
}

// PURE SYSTEM: spatial — reads positions, writes bounding boxes
fn update_spatial(
    spatial: &mut SpatialData,
    positions: &[Vec3],
    meshes: &MeshRegistry,
    render: &RenderData,
    active: &ActiveSet,
) {
    for i in active.active_indices() {
        spatial.bounding_boxes[i] = meshes.get(render.mesh_ids[i]).aabb_at(positions[i]);
    }
}

// PURE: culling — returns indices of visible entities, no GPU dependency
fn cull_visible(
    spatial: &SpatialData,
    active: &ActiveSet,
    frustum: &Frustum,
) -> Vec<usize> {
    active.active_indices()
        .filter(|&i| frustum.contains(&spatial.bounding_boxes[i]))
        .collect()
}

// PURE: build draw calls from visible set — still no GPU types
fn build_draw_calls(
    visible: &[usize],
    render: &RenderData,
    positions: &[Vec3],
    camera: &Camera,
) -> Vec<DrawCall> {
    visible.iter()
        .map(|&i| DrawCall {
            mesh_id: render.mesh_ids[i],
            material_id: render.material_ids[i],
            transform: camera.view_proj() * Mat4::from_translation(positions[i]),
        })
        .sorted_unstable_by_key(|dc| dc.material_id)  // batch by material
        .collect()
}

// SHELL: the only function that touches wgpu — thin, mechanical
fn execute_draws(
    encoder: &mut wgpu::CommandEncoder,
    calls: &[DrawCall],
    gpu: &GpuResources,
) {
    // ... pure translation to GPU commands
}
```

**Performance gains:**
- Physics loop touches 24 bytes/entity (was 200+) → 8x better cache utilization
- Culling is pure → testable, parallelizable with `rayon::par_iter()`
- Bitset active check eliminates per-entity branching
- Systems touch disjoint data → run concurrently without synchronization
- Draw call sorting happens on a small struct (12 bytes) not the full entity

---

## 2. Monolithic Render → Functional Core / Imperative Shell

### Before

```rust
fn render_frame(
    device: &wgpu::Device,
    queue: &wgpu::Queue,
    surface: &wgpu::Surface,
    scene: &Scene,
    camera: &Camera,
    ui: &UiState,
) -> Result<(), wgpu::SurfaceError> {
    let output = surface.get_current_texture()?;
    let view = output.texture.create_view(&Default::default());
    let mut encoder = device.create_command_encoder(&Default::default());

    // Shadow pass — logic + GPU interleaved
    for light in &scene.lights {
        if light.casts_shadow {
            let shadow_view = get_shadow_map(light);
            let mut pass = encoder.begin_render_pass(/* ... */);
            for mesh in &scene.meshes {
                if light.affects(mesh) {
                    pass.set_pipeline(&shadow_pipeline);
                    pass.set_bind_group(0, &light.bind_group, &[]);
                    // ... 15 more lines
                }
            }
        }
    }

    // Main pass — more interleaved logic + GPU
    {
        let mut pass = encoder.begin_render_pass(/* ... */);
        for mesh in &scene.meshes {
            if camera.frustum().contains(&mesh.bounds) {
                // ... 30 lines of set_pipeline, set_bind_group, draw calls
            }
        }
    }

    // Post-process — same pattern
    // UI — same pattern

    queue.submit(std::iter::once(encoder.finish()));
    output.present();
    Ok(())
}
```

**Problems:**
- 150+ line function doing everything. Untestable — needs a live GPU.
- Culling logic buried inside GPU pass recording.
- Adding a new pass means editing this mega-function.
- No way to test "does shadow pass include the right meshes?" without running the GPU.

### After

```rust
// ── PURE LAYER ──────────────────────────────────────

/// Frame plan — a complete description of what to render, no GPU types
struct FramePlan {
    shadow_passes: Vec<ShadowPassPlan>,
    main_pass: MainPassPlan,
    post_process: Vec<PostEffect>,
    ui_draws: Vec<UiElement>,
}

struct ShadowPassPlan {
    light_index: usize,
    casters: Vec<DrawCall>,
}

struct MainPassPlan {
    opaque: Vec<DrawCall>,       // sorted front-to-back
    transparent: Vec<DrawCall>,  // sorted back-to-front
}

/// Pure function — testable without GPU, deterministic
fn plan_frame(scene: &Scene, camera: &Camera, ui: &UiState) -> FramePlan {
    let frustum = camera.frustum();

    let shadow_passes = scene.lights.iter().enumerate()
        .filter(|(_, l)| l.casts_shadow)
        .map(|(i, light)| ShadowPassPlan {
            light_index: i,
            casters: scene.meshes.iter()
                .filter(|m| light.affects(m))
                .map(|m| m.to_shadow_draw_call(light))
                .collect(),
        })
        .collect();

    let (opaque, transparent): (Vec<_>, Vec<_>) = scene.meshes.iter()
        .filter(|m| frustum.contains(&m.bounds))
        .map(|m| m.to_draw_call(camera))
        .partition(|dc| !dc.has_transparency);

    FramePlan {
        shadow_passes,
        main_pass: MainPassPlan {
            opaque: sort_front_to_back(opaque, camera),
            transparent: sort_back_to_front(transparent, camera),
        },
        post_process: scene.active_effects(),
        ui_draws: ui.build_elements(),
    }
}

// ── SHELL LAYER ─────────────────────────────────────

/// Thin — just translates the plan into GPU commands
fn execute_frame(
    device: &wgpu::Device,
    queue: &wgpu::Queue,
    surface: &wgpu::Surface,
    plan: &FramePlan,
    gpu: &GpuResources,
) -> Result<(), wgpu::SurfaceError> {
    let output = surface.get_current_texture()?;
    let view = output.texture.create_view(&Default::default());
    let mut encoder = device.create_command_encoder(&Default::default());

    for shadow in &plan.shadow_passes {
        execute_shadow_pass(&mut encoder, shadow, gpu);
    }
    execute_main_pass(&mut encoder, &plan.main_pass, &view, gpu);
    execute_post_process(&mut encoder, &plan.post_process, gpu);
    execute_ui(&mut encoder, &plan.ui_draws, &view, gpu);

    queue.submit(std::iter::once(encoder.finish()));
    output.present();
    Ok(())
}

// Each sub-executor is 10-15 lines of mechanical GPU translation

// ── TESTS ───────────────────────────────────────────

#[cfg(test)]
mod tests {
    // No GPU needed — pure logic is fully testable
    #[test]
    fn shadow_pass_excludes_non_affected_meshes() {
        let scene = test_scene_with_one_light_and_distant_mesh();
        let plan = plan_frame(&scene, &test_camera(), &UiState::default());
        assert!(plan.shadow_passes[0].casters.is_empty());
    }

    #[test]
    fn transparent_objects_sorted_back_to_front() {
        let scene = test_scene_with_transparent_objects();
        let plan = plan_frame(&scene, &test_camera(), &UiState::default());
        let depths: Vec<f32> = plan.main_pass.transparent.iter()
            .map(|dc| dc.depth)
            .collect();
        assert!(depths.windows(2).all(|w| w[0] >= w[1]));
    }
}
```

**Why this is better:**
- `plan_frame` is ~40 lines of pure logic, fully unit-testable
- `execute_frame` is ~15 lines of mechanical GPU translation
- Adding a new pass = add a field to `FramePlan` + a small executor
- Culling, sorting, batching logic is tested independently of the GPU

---

## 3. Runtime Type Checks → Type-State

### Before

```rust
struct Renderer {
    device: Option<wgpu::Device>,
    queue: Option<wgpu::Queue>,
    surface: Option<wgpu::Surface>,
    pipeline: Option<wgpu::RenderPipeline>,
    is_initialized: bool,
    is_configured: bool,
}

impl Renderer {
    fn render(&self) -> Result<(), RendererError> {
        if !self.is_initialized {
            return Err(RendererError::NotInitialized);
        }
        if !self.is_configured {
            return Err(RendererError::NotConfigured);
        }
        let device = self.device.as_ref().unwrap();  // "safe" because is_initialized
        let pipeline = self.pipeline.as_ref().unwrap();  // "safe" because is_configured
        // ... but are they really safe? What if someone sets is_initialized = true
        // without setting device? Nothing prevents it.
    }
}
```

**Problems:**
- Booleans can be set independently from the data they "protect"
- Every method starts with runtime validation
- `unwrap()` calls that are "logically safe" but not provably safe
- New developers can create invalid states the type system doesn't prevent

### After

```rust
use std::marker::PhantomData;

struct Uninitialized;
struct Configured;
struct Ready;

struct Renderer<State = Uninitialized> {
    _state: PhantomData<State>,
    // Inner data varies by state — no Options needed
    inner: RendererInner,
}

enum RendererInner {
    Empty,
    HasDevice { device: wgpu::Device, queue: wgpu::Queue },
    Full {
        device: wgpu::Device,
        queue: wgpu::Queue,
        surface: wgpu::Surface,
        pipeline: wgpu::RenderPipeline,
    },
}

impl Renderer<Uninitialized> {
    fn new() -> Self {
        Self { _state: PhantomData, inner: RendererInner::Empty }
    }

    fn initialize(self, instance: &wgpu::Instance) -> Result<Renderer<Configured>, GpuError> {
        let adapter = pollster::block_on(instance.request_adapter(/* ... */))?;
        let (device, queue) = pollster::block_on(adapter.request_device(/* ... */))?;
        Ok(Renderer {
            _state: PhantomData,
            inner: RendererInner::HasDevice { device, queue },
        })
    }
}

impl Renderer<Configured> {
    fn configure_surface(self, window: &Window) -> Result<Renderer<Ready>, GpuError> {
        // ... create surface and pipeline
        Ok(Renderer { _state: PhantomData, inner: RendererInner::Full { /* ... */ } })
    }
}

impl Renderer<Ready> {
    // No runtime checks. If you have a Renderer<Ready>, it's fully initialized.
    // The type system guarantees it. Zero-cost.
    fn render(&self) -> Result<(), wgpu::SurfaceError> {
        let RendererInner::Full { device, queue, surface, pipeline } = &self.inner else {
            unreachable!() // provably unreachable by type-state
        };
        // ... render without any Option unwrapping or bool checking
    }
}

// Compile-time enforcement:
// Renderer::new().render();                    // ERROR: render() not on Uninitialized
// Renderer::new().configure_surface(window);   // ERROR: configure_surface() not on Uninitialized
```

---

## 4. Scattered Allocations → Arena-Scoped

### Before

```rust
fn process_frame(scene: &Scene, camera: &Camera) -> Vec<DrawCall> {
    let mut calls = Vec::new();                          // alloc 1
    let visible = get_visible_entities(scene, camera);   // alloc 2 (internal Vec)
    let sorted = sort_by_material(&visible);             // alloc 3 (new Vec)

    for entity in &sorted {
        let transform = compute_transform(entity);       // might alloc (Mat4 is stack, but sub-calls?)
        let name = format!("draw_{}", entity.name());    // alloc 4 × N (String per entity!)
        calls.push(DrawCall {
            transform,
            label: name,
            // ...
        });
    }

    calls  // returned — this allocation is justified
}
// Per frame: 3 + N allocations. At 1000 entities = 1003 mallocs/frame.
```

### After

```rust
use bumpalo::Bump;

struct FrameAllocator {
    bump: Bump,
}

impl FrameAllocator {
    fn reset(&mut self) {
        self.bump.reset();  // O(1) — just moves the pointer back
    }
}

fn process_frame<'a>(
    scene: &Scene,
    camera: &Camera,
    arena: &'a FrameAllocator,
    // Reusable output buffer — not allocated per frame
    out: &mut Vec<DrawCall>,
) {
    out.clear();  // O(1) — capacity retained from last frame

    let frustum = camera.frustum();

    // No intermediate allocations — iterator pipeline feeds directly into out
    out.extend(
        scene.entities.iter()
            .filter(|e| frustum.contains(&e.bounds))
            .sorted_unstable_by_key(|e| e.material_id())
            .map(|e| DrawCall {
                transform: compute_transform(e),
                // Arena-allocated string — freed with arena.reset(), not individual drop
                label: arena.bump.alloc_str(&format!("draw_{}", e.name())),
                // ...
            })
    );
}

// Game loop:
let mut arena = FrameAllocator { bump: Bump::new() };
let mut draw_calls = Vec::with_capacity(2048);  // allocated once

loop {
    arena.reset();  // one "free" for all frame temporaries
    process_frame(&scene, &camera, &arena, &mut draw_calls);
    execute(&draw_calls);
}
// Per frame: 0 heap allocations. Arena reset is O(1). Vec reuses capacity.
```

---

## 5. Stringly-Typed Errors → Algebraic Domain Errors

### Before

```rust
fn load_shader(path: &str) -> Result<Shader, String> {
    let source = std::fs::read_to_string(path)
        .map_err(|e| format!("Failed to read shader: {}", e))?;

    let module = compile(&source)
        .map_err(|e| format!("Shader compilation failed: {}", e))?;

    validate(&module)
        .map_err(|e| format!("Shader validation error: {}", e))?;

    Ok(Shader::new(module))
}

// Caller:
match load_shader("main.wgsl") {
    Err(msg) => {
        // What kind of error? Have to parse the string.
        if msg.contains("read") { /* retry? */ }
        else if msg.contains("compilation") { /* show in editor? */ }
        // Fragile, untestable, refactor-hostile
    }
    Ok(s) => { /* ... */ }
}
```

### After

```rust
use std::path::PathBuf;

#[derive(Debug, thiserror::Error)]
enum ShaderError {
    #[error("cannot read shader at {path}")]
    Io {
        path: PathBuf,
        #[source]
        source: std::io::Error,
    },

    #[error("compilation failed at line {line}: {message}")]
    Compilation {
        line: u32,
        message: String,
    },

    #[error("validation error: {kind}")]
    Validation {
        kind: ValidationErrorKind,
    },
}

#[derive(Debug, thiserror::Error)]
enum ValidationErrorKind {
    #[error("binding {binding} in group {group} conflicts")]
    BindingConflict { group: u32, binding: u32 },
    #[error("unsupported feature: {0}")]
    UnsupportedFeature(&'static str),
}

fn load_shader(path: &Path) -> Result<Shader, ShaderError> {
    let source = std::fs::read_to_string(path)
        .map_err(|source| ShaderError::Io { path: path.to_owned(), source })?;

    let module = compile(&source)?;  // returns ShaderError::Compilation
    validate(&module)?;              // returns ShaderError::Validation

    Ok(Shader::new(module))
}

// Caller — exhaustive matching, compiler-enforced:
match load_shader(Path::new("main.wgsl")) {
    Err(ShaderError::Io { path, source }) => {
        log::warn!("Shader file not found: {path:?}, using fallback");
        load_fallback_shader()
    }
    Err(ShaderError::Compilation { line, message }) => {
        editor.highlight_error(line, &message);  // precise error location
        Err(ShaderError::Compilation { line, message })
    }
    Err(ShaderError::Validation { kind }) => {
        // Each validation error variant can be handled specifically
        match kind {
            ValidationErrorKind::BindingConflict { group, binding } => {
                log::error!("Fix binding {binding} in group {group}");
            }
            ValidationErrorKind::UnsupportedFeature(feat) => {
                log::warn!("Feature {feat} not supported, disabling");
            }
        }
        Err(ShaderError::Validation { kind })
    }
    Ok(shader) => Ok(shader),
}
```

**Why algebraic errors win:**
- Adding a new error variant forces every match site to handle it (no silent ignoring)
- Error data is structured, not parsed from strings
- Errors compose via `?` — the happy path reads linearly
- Testing is trivial: construct the error variant directly, assert on the match arm
