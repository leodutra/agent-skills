# Patterns Reference

Detailed code patterns for functional, performance-first Rust.
Read this file when implementing specific patterns mentioned in SKILL.md.

## Table of Contents

1. Type-State Pattern
2. Zero-Cost Iterator Pipelines
3. Arena Allocation
4. SoA (Struct of Arrays)
5. Newtype Safety
6. Builder Pattern for GPU Resources
7. Composition Over Inheritance
8. Tail-Recursive Style via Iterators
9. Monadic Error Chains
10. Slot Map / Generational Indices
11. Data-Oriented Design Principles

---

## 1. Type-State Pattern

Encode valid state transitions in the type system. Invalid transitions
become compile errors, not runtime panics.

```rust
use std::marker::PhantomData;

// States — zero-sized types, no runtime cost
struct Uninitialized;
struct Configured;
struct Ready;

struct Pipeline<S> {
    device: wgpu::Device,
    inner: Option<wgpu::RenderPipeline>,
    _state: PhantomData<S>,
}

impl Pipeline<Uninitialized> {
    fn new(device: wgpu::Device) -> Self {
        Self { device, inner: None, _state: PhantomData }
    }

    fn configure(self, desc: &PipelineDescriptor) -> Result<Pipeline<Configured>, ShaderError> {
        // validate and set up — consumes self, returns new state
        let layout = validate_layout(&self.device, desc)?;
        Ok(Pipeline {
            device: self.device,
            inner: None,
            _state: PhantomData,
        })
    }
}

impl Pipeline<Configured> {
    fn build(self) -> Pipeline<Ready> {
        let pipeline = create_render_pipeline(&self.device);
        Pipeline {
            device: self.device,
            inner: Some(pipeline),
            _state: PhantomData,
        }
    }
}

impl Pipeline<Ready> {
    fn bind<'a>(&'a self, pass: &mut wgpu::RenderPass<'a>) {
        pass.set_pipeline(self.inner.as_ref().unwrap());
    }
}

// Compile-time enforcement:
// Pipeline::new(dev).bind(&mut pass);  // ERROR: bind() not on Uninitialized
// Pipeline::new(dev).configure(&desc)?.configure(&desc)?;  // ERROR: configure() not on Configured
```

**Cost:** Zero. PhantomData is ZST. State transitions are moves, not allocations.

---

## 2. Zero-Cost Iterator Pipelines

Iterators fuse into a single pass with no intermediate allocations.
The compiler unrolls and vectorizes the fused loop.

```rust
// Processing a mesh: filter visible, transform, batch by material
fn prepare_draw_batches<'a>(
    meshes: &'a [MeshInstance],
    frustum: &Frustum,
    camera: &Camera,
) -> impl Iterator<Item = DrawBatch> + 'a {
    meshes.iter()
        .filter(move |m| frustum.intersects(&m.bounding_sphere))
        .map(move |m| DrawCall {
            mesh_id: m.mesh_id,
            transform: camera.view_proj() * m.world_transform,
            material: m.material_id,
            depth: camera.depth_of(m.position),
        })
        // Chunk into batches by material for instanced drawing
        // Note: this requires collect + sort since iterator is lazy
        .sorted_unstable_by_key(|dc| dc.material)
        .chunk_by(|dc| dc.material)
        .into_iter()
        .map(|(material, group)| DrawBatch {
            material,
            calls: group.collect(),
        })
}
```

**When to break the pattern:** If `chunks_exact()` or `array_windows()`
would let LLVM auto-vectorize but the iterator version doesn't, use the
slice-based version. Check godbolt.

### Collecting Into Pre-Allocated Buffers

```rust
// AVOID: allocates every frame
let results: Vec<_> = iter.collect();

// PREFER: reuse across frames
frame_buffer.clear();
frame_buffer.extend(iter);
```

---

## 3. Arena Allocation

For per-frame temporaries, use a bump allocator. All allocations are O(1),
and deallocation is a single pointer reset.

```rust
use bumpalo::Bump;

struct FrameArena {
    bump: Bump,
}

impl FrameArena {
    fn new_frame(&mut self) {
        self.bump.reset(); // O(1) — just resets the pointer
    }

    fn alloc_slice<T: Copy>(&self, data: &[T]) -> &[T] {
        self.bump.alloc_slice_copy(data)
    }

    fn alloc_str(&self, s: &str) -> &str {
        self.bump.alloc_str(s)
    }
}

// Usage in render loop:
fn render_frame(arena: &mut FrameArena, scene: &Scene) {
    arena.new_frame();

    // All allocations below are bump-allocated, freed together at next frame
    let transforms = arena.alloc_slice(&compute_transforms(scene));
    let draw_calls = arena.alloc_slice(&build_draw_calls(scene, transforms));
    execute(draw_calls);
}
```

**Rule:** If data doesn't outlive the frame, it goes in the arena. Period.

---

## 4. SoA (Struct of Arrays) for Cache-Friendly GPU Data

AoS (Array of Structs) scatters fields across cache lines.
SoA groups same-typed fields together for sequential access.

```rust
// AOS — bad for iteration over just positions
struct ParticleAoS {
    position: [f32; 3],
    velocity: [f32; 3],
    color: [f32; 4],
    lifetime: f32,
}
// Iterating positions touches 40 bytes per particle, uses 12

// SOA — cache-optimal for per-field iteration
struct ParticleSystem {
    positions: Vec<[f32; 3]>,   // contiguous, SIMD-friendly
    velocities: Vec<[f32; 3]>,
    colors: Vec<[f32; 4]>,
    lifetimes: Vec<f32>,
    count: usize,
}

impl ParticleSystem {
    fn update_positions(&mut self, dt: f32) {
        // Iterates two contiguous arrays — cache-optimal, auto-vectorizable
        for (pos, vel) in self.positions.iter_mut().zip(&self.velocities) {
            pos[0] += vel[0] * dt;
            pos[1] += vel[1] * dt;
            pos[2] += vel[2] * dt;
        }
    }

    fn with_capacity(cap: usize) -> Self {
        Self {
            positions: Vec::with_capacity(cap),
            velocities: Vec::with_capacity(cap),
            colors: Vec::with_capacity(cap),
            lifetimes: Vec::with_capacity(cap),
            count: 0,
        }
    }
}
```

**Guideline:** Use SoA when you iterate over a single field at a time
(physics, culling, sorting). Use AoS when you always access all fields
together (serialization, GPU upload of interleaved vertex data).

---

## 5. Newtype Safety

Prevent mixing semantically different values that share a type.

```rust
// Without newtypes: silent bugs
fn set_viewport(x: f32, y: f32, w: f32, h: f32) { ... }

// With newtypes: compile-time protection, zero runtime cost
#[derive(Debug, Clone, Copy)]
struct ScreenPos(glam::Vec2);

#[derive(Debug, Clone, Copy)]
struct WorldPos(glam::Vec3);

#[derive(Debug, Clone, Copy)]
struct NdcPos(glam::Vec2); // Normalized Device Coordinates

impl WorldPos {
    fn project(self, view_proj: &glam::Mat4) -> NdcPos {
        let clip = *view_proj * self.0.extend(1.0);
        NdcPos(glam::vec2(clip.x / clip.w, clip.y / clip.w))
    }
}

impl NdcPos {
    fn to_screen(self, viewport: &Viewport) -> ScreenPos {
        ScreenPos(glam::vec2(
            (self.0.x * 0.5 + 0.5) * viewport.width,
            (self.0.y * -0.5 + 0.5) * viewport.height,
        ))
    }
}

// WorldPos::project().to_screen() — the only valid conversion chain
// ScreenPos cannot be used where WorldPos is expected — compile error
```

**Cost:** Zero. `#[repr(transparent)]` guarantees identical layout.

---

## 6. Builder Pattern for GPU Resources

GPU resource creation involves many optional parameters. Builders make
this ergonomic without runtime overhead.

```rust
struct TextureBuilder<'a> {
    device: &'a wgpu::Device,
    size: wgpu::Extent3d,
    format: wgpu::TextureFormat,
    usage: wgpu::TextureUsages,
    label: Option<&'a str>,
    mip_levels: u32,
    sample_count: u32,
}

impl<'a> TextureBuilder<'a> {
    fn new(device: &'a wgpu::Device, width: u32, height: u32) -> Self {
        Self {
            device,
            size: wgpu::Extent3d { width, height, depth_or_array_layers: 1 },
            format: wgpu::TextureFormat::Rgba8UnormSrgb,
            usage: wgpu::TextureUsages::TEXTURE_BINDING | wgpu::TextureUsages::COPY_DST,
            label: None,
            mip_levels: 1,
            sample_count: 1,
        }
    }

    fn format(mut self, format: wgpu::TextureFormat) -> Self {
        self.format = format;
        self
    }

    fn usage(mut self, usage: wgpu::TextureUsages) -> Self {
        self.usage = usage;
        self
    }

    fn label(mut self, label: &'a str) -> Self {
        self.label = Some(label);
        self
    }

    fn with_mipmaps(mut self) -> Self {
        self.mip_levels = (self.size.width.max(self.size.height) as f32).log2() as u32 + 1;
        self
    }

    fn build(self) -> wgpu::Texture {
        self.device.create_texture(&wgpu::TextureDescriptor {
            label: self.label,
            size: self.size,
            mip_level_count: self.mip_levels,
            sample_count: self.sample_count,
            dimension: wgpu::TextureDimension::D2,
            format: self.format,
            usage: self.usage,
            view_formats: &[],
        })
    }
}

// Usage — reads like a spec:
let depth = TextureBuilder::new(&device, 1920, 1080)
    .format(wgpu::TextureFormat::Depth32Float)
    .usage(wgpu::TextureUsages::RENDER_ATTACHMENT)
    .label("depth_buffer")
    .build();
```

**Cost:** Builder is consumed on `.build()`. All intermediate state lives on the stack.

---

## 7. Composition Over Inheritance

Rust has no inheritance. Compose behavior through traits and generics.

```rust
// Trait = interface contract
trait Renderable {
    fn vertex_buffer(&self) -> &wgpu::Buffer;
    fn index_buffer(&self) -> &wgpu::Buffer;
    fn index_count(&self) -> u32;
    fn bind_group(&self) -> &wgpu::BindGroup;
}

trait Transformable {
    fn world_matrix(&self) -> glam::Mat4;
}

// Compose traits via bounds — not inheritance
fn draw_object<T: Renderable + Transformable>(
    pass: &mut wgpu::RenderPass,
    object: &T,
    uniform_buffer: &wgpu::Buffer,
    queue: &wgpu::Queue,
) {
    queue.write_buffer(uniform_buffer, 0, bytemuck::bytes_of(&object.world_matrix()));
    pass.set_vertex_buffer(0, object.vertex_buffer().slice(..));
    pass.set_index_buffer(object.index_buffer().slice(..), wgpu::IndexFormat::Uint32);
    pass.set_bind_group(0, object.bind_group(), &[]);
    pass.draw_indexed(0..object.index_count(), 0, 0..1);
}
```

---

## 8. Tail-Recursive Style via Iterators

Rust doesn't guarantee TCO. Express recursive patterns as iterators
or `loop` + accumulator instead.

```rust
// AVOID: recursive, stack-dependent
fn find_root(node: &SceneNode) -> &SceneNode {
    match &node.parent {
        Some(parent) => find_root(parent),
        None => node,
    }
}

// PREFER: iterative, stack-safe, same semantics
fn find_root(mut node: &SceneNode) -> &SceneNode {
    while let Some(ref parent) = node.parent {
        node = parent;
    }
    node
}

// For tree traversal, use an explicit stack (Vec) instead of call stack:
fn traverse_depth_first(root: &SceneNode) -> impl Iterator<Item = &SceneNode> {
    let mut stack = vec![root];
    std::iter::from_fn(move || {
        let node = stack.pop()?;
        stack.extend(node.children.iter().rev());
        Some(node)
    })
}
```

---

## 9. Monadic Error Chains

Use `?`, `map`, `and_then` to chain fallible operations as a linear pipeline.

```rust
fn load_texture(
    device: &wgpu::Device,
    queue: &wgpu::Queue,
    path: &Path,
) -> Result<Texture, AssetError> {
    let bytes = std::fs::read(path)
        .map_err(|e| AssetError::Io { path: path.to_owned(), source: e })?;

    let image = image::load_from_memory(&bytes)
        .map_err(|e| AssetError::Decode { path: path.to_owned(), source: e })?;

    let rgba = image.to_rgba8();
    let dimensions = image.dimensions();

    let texture = TextureBuilder::new(device, dimensions.0, dimensions.1)
        .label(path.file_name().and_then(|n| n.to_str()).unwrap_or("texture"))
        .with_mipmaps()
        .build();

    queue.write_texture(
        texture.as_image_copy(),
        &rgba,
        data_layout(dimensions),
        extent(dimensions),
    );

    Ok(Texture::new(texture, device))
}
```

Each step is independently testable. The error type is algebraic and specific.

---

## 10. Slot Map / Generational Indices

For GPU resource handles, use generational indices instead of raw pointers
or Rc. This prevents use-after-free at the type level.

```rust
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
struct Handle<T> {
    index: u32,
    generation: u32,
    _marker: PhantomData<T>,
}

struct SlotMap<T> {
    entries: Vec<Option<(u32, T)>>, // (generation, value)
    free_list: Vec<u32>,
    current_generation: u32,
}

impl<T> SlotMap<T> {
    fn insert(&mut self, value: T) -> Handle<T> {
        let index = self.free_list.pop().unwrap_or_else(|| {
            self.entries.push(None);
            (self.entries.len() - 1) as u32
        });
        self.current_generation += 1;
        self.entries[index as usize] = Some((self.current_generation, value));
        Handle { index, generation: self.current_generation, _marker: PhantomData }
    }

    fn get(&self, handle: Handle<T>) -> Option<&T> {
        self.entries.get(handle.index as usize)
            .and_then(|slot| slot.as_ref())
            .filter(|(gen, _)| *gen == handle.generation)
            .map(|(_, val)| val)
    }

    fn remove(&mut self, handle: Handle<T>) -> Option<T> {
        let slot = self.entries.get_mut(handle.index as usize)?;
        match slot.take() {
            Some((gen, val)) if gen == handle.generation => {
                self.free_list.push(handle.index);
                Some(val)
            }
            other => {
                *slot = other; // put it back
                None
            }
        }
    }
}
```

**Why:** GPU resources are created and destroyed dynamically. Generational
indices give you O(1) access, O(1) insert/remove, cache-friendly storage,
and use-after-free detection — all without reference counting overhead.

---

## 11. Data-Oriented Design Principles

Think in terms of data transformations, not object hierarchies.

**Before (OOP mindset):**
```rust
// Each entity is a bag of methods operating on scattered fields
impl Enemy {
    fn update(&mut self, dt: f32) {
        self.ai.think(dt);        // touches AI data
        self.physics.step(dt);    // touches physics data
        self.animation.tick(dt);  // touches animation data
        self.render.prepare();    // touches render data
    }
}
```

**After (data-oriented, functional):**
```rust
// Each system is a pure-ish function operating on contiguous data
fn update_ai(ai_components: &mut [AiState], world: &WorldState, dt: f32) { ... }
fn update_physics(positions: &mut [Vec3], velocities: &[Vec3], dt: f32) { ... }
fn update_animations(anims: &mut [AnimState], dt: f32) { ... }
fn prepare_render(positions: &[Vec3], meshes: &[MeshId]) -> Vec<DrawCall> { ... }
```

Each function touches only the data it needs. Cache utilization goes up.
Parallelism becomes trivial (systems touching disjoint data run concurrently).
Testing requires no entity scaffolding — just slices of components.
