# wgpu Idioms Reference

wgpu-specific patterns for functional, performance-first Rust GPU code.
Read this when implementing GPU pipelines, resource management, or shader integration.

## Table of Contents

1. Bind Group Layout Composition
2. Render Pass Structure
3. Compute Pass Structure
4. Host/Shader Contract Review
5. Buffer Management
6. Pipeline Caching
7. WGSL Shader Organization
8. Surface Configuration & Resize
9. Multi-Pass Rendering
10. GPU Profiling Integration
11. Resource Lifetime Management

---

## 1. Bind Group Layout Composition

Compose bind group layouts by frequency of update — not by logical grouping.

```rust
// Group 0: Per-frame (camera, time, globals) — updated once per frame
// Group 1: Per-material (textures, samplers, material params) — updated per material switch
// Group 2: Per-object (transforms, instance data) — updated per draw call

fn create_per_frame_layout(device: &wgpu::Device) -> wgpu::BindGroupLayout {
    device.create_bind_group_layout(&wgpu::BindGroupLayoutDescriptor {
        label: Some("per_frame_layout"),
        entries: &[
            // Camera uniform buffer
            wgpu::BindGroupLayoutEntry {
                binding: 0,
                visibility: wgpu::ShaderStages::VERTEX | wgpu::ShaderStages::FRAGMENT,
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Uniform,
                    has_dynamic_offset: false,
                    min_binding_size: std::num::NonZeroU64::new(
                        std::mem::size_of::<CameraUniforms>() as u64
                    ),
                },
                count: None,
            },
            // Time / globals
            wgpu::BindGroupLayoutEntry {
                binding: 1,
                visibility: wgpu::ShaderStages::all(),
                ty: wgpu::BindingType::Buffer {
                    ty: wgpu::BufferBindingType::Uniform,
                    has_dynamic_offset: false,
                    min_binding_size: std::num::NonZeroU64::new(
                        std::mem::size_of::<FrameUniforms>() as u64
                    ),
                },
                count: None,
            },
        ],
    })
}
```

**Why frequency-based grouping:** Changing bind group 2 doesn't invalidate
groups 0 and 1. Minimizes GPU state changes, which is the #1 draw call
optimization.

---

## 2. Render Pass Structure

Separate render pass *description* (pure) from *execution* (side-effectful).

```rust
// PURE: Describes what the pass will look like
struct RenderPassConfig {
    color_format: wgpu::TextureFormat,
    depth_format: Option<wgpu::TextureFormat>,
    sample_count: u32,
    clear_color: wgpu::Color,
}

impl RenderPassConfig {
    fn color_attachment<'a>(
        &self,
        view: &'a wgpu::TextureView,
        resolve_target: Option<&'a wgpu::TextureView>,
    ) -> wgpu::RenderPassColorAttachment<'a> {
        wgpu::RenderPassColorAttachment {
            view,
            resolve_target,
            ops: wgpu::Operations {
                load: wgpu::LoadOp::Clear(self.clear_color),
                store: wgpu::StoreOp::Store,
            },
        }
    }

    fn depth_attachment<'a>(
        &self,
        view: &'a wgpu::TextureView,
    ) -> Option<wgpu::RenderPassDepthStencilAttachment<'a>> {
        self.depth_format.map(|_| wgpu::RenderPassDepthStencilAttachment {
            view,
            depth_ops: Some(wgpu::Operations {
                load: wgpu::LoadOp::Clear(1.0),
                store: wgpu::StoreOp::Store,
            }),
            stencil_ops: None,
        })
    }
}

// SHELL: Executes the pass
fn execute_render_pass(
    encoder: &mut wgpu::CommandEncoder,
    config: &RenderPassConfig,
    color_view: &wgpu::TextureView,
    depth_view: Option<&wgpu::TextureView>,
    draw_fn: impl FnOnce(&mut wgpu::RenderPass),
) {
    let color_attachment = config.color_attachment(color_view, None);
    let depth_attachment = depth_view.and_then(|v| config.depth_attachment(v));

    let mut pass = encoder.begin_render_pass(&wgpu::RenderPassDescriptor {
        label: Some("main_pass"),
        color_attachments: &[Some(color_attachment)],
        depth_stencil_attachment: depth_attachment,
        timestamp_writes: None,
        occlusion_query_set: None,
    });

    draw_fn(&mut pass);
}
```

---

## 3. Compute Pass Structure

Same pattern — describe the dispatch purely, execute thinly.

```rust
struct ComputeDispatch {
    pipeline_key: PipelineKey,
    bind_groups: Vec<BindGroupKey>,
    workgroups: [u32; 3],
}

// PURE: decide what to dispatch
fn plan_particle_update(particle_count: u32) -> ComputeDispatch {
    let workgroup_size = 256;
    let workgroups_x = (particle_count + workgroup_size - 1) / workgroup_size;

    ComputeDispatch {
        pipeline_key: PipelineKey::ParticleUpdate,
        bind_groups: vec![BindGroupKey::ParticleData],
        workgroups: [workgroups_x, 1, 1],
    }
}

// SHELL: execute
fn execute_compute(
    encoder: &mut wgpu::CommandEncoder,
    dispatch: &ComputeDispatch,
    resources: &GpuResources,
) {
    let mut pass = encoder.begin_compute_pass(&wgpu::ComputePassDescriptor {
        label: Some("compute_pass"),
        timestamp_writes: None,
    });

    let pipeline = resources.get_compute_pipeline(dispatch.pipeline_key);
    pass.set_pipeline(pipeline);

    for (i, key) in dispatch.bind_groups.iter().enumerate() {
        pass.set_bind_group(i as u32, resources.get_bind_group(*key), &[]);
    }

    pass.dispatch_workgroups(
        dispatch.workgroups[0],
        dispatch.workgroups[1],
        dispatch.workgroups[2],
    );
}
```

---

## 4. Host/Shader Contract Review

Review GPU bindings as one contract, not three isolated snippets.

Checklist:
- Each WGSL binding index exists in the Rust bind group layout
- `read_only` matches WGSL `read` vs `read_write`
- shader-stage visibility matches actual usage
- bind group entries point at the intended buffers for each binding
- aggregate outputs such as indirect args have a single owning writer

### Indirect Draw Ownership

If a compute pass writes indirect arguments:
- make one pass the sole writer of `instance_count`
- initialize the remaining fields deterministically in that same pass or on the CPU
- remove stale bindings from earlier passes once ownership moves

This prevents the common failure mode where the shader changes but Rust still binds the old
writer path.

---

## 5. Buffer Management

### Staging Buffer Pattern

Never map GPU buffers directly for writing. Use a staging belt or
write through the queue.

```rust
// For small, frequent updates (uniforms): use queue.write_buffer
fn update_camera_uniform(
    queue: &wgpu::Queue,
    buffer: &wgpu::Buffer,
    camera: &Camera,
) {
    let uniforms = CameraUniforms::from(camera);
    queue.write_buffer(buffer, 0, bytemuck::bytes_of(&uniforms));
}

// For large, infrequent uploads (mesh data): staging buffer + copy
fn upload_mesh_data(
    device: &wgpu::Device,
    queue: &wgpu::Queue,
    encoder: &mut wgpu::CommandEncoder,
    target: &wgpu::Buffer,
    data: &[Vertex],
) {
    let staging = device.create_buffer_init(&wgpu::util::BufferInitDescriptor {
        label: Some("staging"),
        contents: bytemuck::cast_slice(data),
        usage: wgpu::BufferUsages::COPY_SRC,
    });

    encoder.copy_buffer_to_buffer(
        &staging, 0,
        target, 0,
        (data.len() * std::mem::size_of::<Vertex>()) as u64,
    );
    // staging buffer is dropped — GPU will keep it alive until copy completes
}
```

### Ring Buffer for Dynamic Data

```rust
struct RingBuffer {
    buffer: wgpu::Buffer,
    capacity: u64,
    write_offset: u64,
    alignment: u64,
}

impl RingBuffer {
    fn allocate(&mut self, size: u64) -> Option<u64> {
        let aligned_size = align_up(size, self.alignment);
        let offset = self.write_offset;

        if offset + aligned_size > self.capacity {
            // Wrap around — only if the data fits from the start
            if aligned_size > self.capacity {
                return None;
            }
            self.write_offset = aligned_size;
            Some(0)
        } else {
            self.write_offset = offset + aligned_size;
            Some(offset)
        }
    }

    fn reset(&mut self) {
        self.write_offset = 0;
    }
}

fn align_up(value: u64, alignment: u64) -> u64 {
    (value + alignment - 1) & !(alignment - 1)
}
```

---

## 6. Pipeline Caching

Create pipelines lazily, cache by a hashable key. Pipeline creation is
expensive — never do it during rendering.

```rust
use std::collections::HashMap;

#[derive(Debug, Clone, Hash, PartialEq, Eq)]
struct RenderPipelineKey {
    shader: ShaderId,
    vertex_layout: VertexLayoutId,
    color_format: wgpu::TextureFormat,
    depth_format: Option<wgpu::TextureFormat>,
    blend_mode: BlendMode,
    cull_mode: Option<wgpu::Face>,
    topology: wgpu::PrimitiveTopology,
}

struct PipelineCache {
    render_pipelines: HashMap<RenderPipelineKey, wgpu::RenderPipeline>,
    compute_pipelines: HashMap<ComputePipelineKey, wgpu::ComputePipeline>,
}

impl PipelineCache {
    fn get_or_create_render(
        &mut self,
        device: &wgpu::Device,
        key: &RenderPipelineKey,
        layouts: &LayoutRegistry,
        shaders: &ShaderRegistry,
    ) -> &wgpu::RenderPipeline {
        // clone: entry insertion requires an owned key at the cache boundary
        self.render_pipelines.entry(key.clone()).or_insert_with(|| {
            // Expensive — only happens once per unique key
            create_render_pipeline(device, key, layouts, shaders)
        })
    }

    /// Pre-warm during loading screen, not during gameplay
    fn warm_up(
        &mut self,
        device: &wgpu::Device,
        keys: &[RenderPipelineKey],
        layouts: &LayoutRegistry,
        shaders: &ShaderRegistry,
    ) {
        for key in keys {
            self.get_or_create_render(device, key, layouts, shaders);
        }
    }
}
```

---

## 7. WGSL Shader Organization

Keep shader code composable with includes (via string concatenation)
and consistent binding conventions.

```rust
// Shared definitions — prepended to all shaders
const COMMON_WGSL: &str = r#"
    struct CameraUniforms {
        view: mat4x4<f32>,
        proj: mat4x4<f32>,
        view_proj: mat4x4<f32>,
        position: vec3<f32>,
        near: f32,
        far: f32,
    }

    @group(0) @binding(0) var<uniform> camera: CameraUniforms;
"#;

// Per-material fragment — concatenated after common
const PBR_FRAGMENT_WGSL: &str = r#"
    @group(1) @binding(0) var base_color_texture: texture_2d<f32>;
    @group(1) @binding(1) var base_color_sampler: sampler;
    // ...
"#;

fn build_shader_source(modules: &[&str]) -> String {
    modules.join("\n")
}

fn create_shader(device: &wgpu::Device, modules: &[&str], label: &str) -> wgpu::ShaderModule {
    let source = build_shader_source(modules);
    device.create_shader_module(wgpu::ShaderModuleDescriptor {
        label: Some(label),
        source: wgpu::ShaderSource::Wgsl(source.into()),
    })
}

// Usage:
let pbr_shader = create_shader(&device, &[COMMON_WGSL, PBR_FRAGMENT_WGSL], "pbr_shader");
```

**Convention:** Group 0 = per-frame, Group 1 = per-material, Group 2 = per-object.
This convention is shared between Rust and WGSL — never violate it.

---

## 8. Surface Configuration & Resize

Handle resize purely — compute the new config, then apply it.

```rust
struct SurfaceConfig {
    width: u32,
    height: u32,
    format: wgpu::TextureFormat,
    present_mode: wgpu::PresentMode,
}

impl SurfaceConfig {
    /// Pure — computes the new config from a resize event
    fn from_resize(physical_size: winit::dpi::PhysicalSize<u32>, format: wgpu::TextureFormat) -> Option<Self> {
        if physical_size.width == 0 || physical_size.height == 0 {
            return None; // minimized — skip reconfiguration
        }
        Some(Self {
            width: physical_size.width,
            height: physical_size.height,
            format,
            present_mode: wgpu::PresentMode::Fifo, // vsync, most compatible
        })
    }

    /// Side-effectful — applies the config
    fn apply(&self, surface: &wgpu::Surface, device: &wgpu::Device) {
        surface.configure(device, &wgpu::SurfaceConfiguration {
            usage: wgpu::TextureUsages::RENDER_ATTACHMENT,
            format: self.format,
            width: self.width,
            height: self.height,
            present_mode: self.present_mode,
            alpha_mode: wgpu::CompositeAlphaMode::Auto,
            view_formats: vec![],
            desired_maximum_frame_latency: 2,
        });
    }

    fn aspect_ratio(&self) -> f32 {
        self.width as f32 / self.height as f32
    }
}
```

---

## 9. Multi-Pass Rendering

For GPU-driven pipelines such as culling, scan, and compaction, model each pass as a narrow
data transformation:

```text
flags -> chunk_counts -> chunk_offsets/block_sums -> block_offsets/indirect_args -> compacted_output
```

Rules:
- keep outputs narrow and intentional
- prefer one responsibility per pass over a pass that mutates unrelated buffers
- assert scan hierarchy limits in Rust next to dispatch math
- use separate shaders when passes have different ownership or hazard profiles

Structure multi-pass as a sequence of pure pass descriptions.

```rust
enum PassKind {
    Shadow { light_index: usize },
    GBuffer,
    Lighting,
    PostProcess { effects: Vec<PostEffect> },
    Ui,
}

struct FramePlan {
    passes: Vec<PassKind>,
}

/// PURE: determine which passes are needed this frame
fn plan_frame(scene: &Scene, config: &RenderConfig) -> FramePlan {
    let mut passes = Vec::new();

    // Shadow passes for each shadow-casting light
    for (i, light) in scene.lights.iter().enumerate() {
        if light.casts_shadows {
            passes.push(PassKind::Shadow { light_index: i });
        }
    }

    passes.push(PassKind::GBuffer);
    passes.push(PassKind::Lighting);

    if !config.post_effects.is_empty() {
        passes.push(PassKind::PostProcess {
            // clone: FramePlan owns its pass descriptions beyond the config borrow
            effects: config.post_effects.clone(),
        });
    }

    passes.push(PassKind::Ui);

    FramePlan { passes }
}

/// SHELL: execute the plan
fn execute_frame(
    encoder: &mut wgpu::CommandEncoder,
    plan: &FramePlan,
    resources: &GpuResources,
) {
    for pass in &plan.passes {
        match pass {
            PassKind::Shadow { light_index } => execute_shadow_pass(encoder, *light_index, resources),
            PassKind::GBuffer => execute_gbuffer_pass(encoder, resources),
            PassKind::Lighting => execute_lighting_pass(encoder, resources),
            PassKind::PostProcess { effects } => execute_post_process(encoder, effects, resources),
            PassKind::Ui => execute_ui_pass(encoder, resources),
        }
    }
}
```

---

## 10. GPU Profiling Integration

GPU timings are only useful when they isolate the work being discussed.

- bracket actual compute or render work with timestamps
- keep query index ownership obvious and documented
- separate culling, draw, and composite timings when investigating regressions
- if a metric is placeholder or invalid, expose that rather than reporting misleading numbers

Wrap timing queries as composable decorators, not invasive modifications.

```rust
struct GpuProfiler {
    query_set: wgpu::QuerySet,
    resolve_buffer: wgpu::Buffer,
    readback_buffer: wgpu::Buffer,
    next_query: u32,
    labels: Vec<String>,
}

impl GpuProfiler {
    fn scope<'a>(
        &'a mut self,
        encoder: &'a mut wgpu::CommandEncoder,
        label: &str,
    ) -> ProfileScope<'a> {
        let begin_index = self.next_query;
        self.next_query += 2;
        self.labels.push(label.to_string());
        encoder.write_timestamp(&self.query_set, begin_index);
        ProfileScope { profiler: self, encoder, end_index: begin_index + 1 }
    }
}

struct ProfileScope<'a> {
    profiler: &'a mut GpuProfiler,
    encoder: &'a mut wgpu::CommandEncoder,
    end_index: u32,
}

impl Drop for ProfileScope<'_> {
    fn drop(&mut self) {
        self.encoder.write_timestamp(&self.profiler.query_set, self.end_index);
    }
}
```

---

## 11. Resource Lifetime Management

Use a deferred deletion queue to safely destroy GPU resources.

```rust
struct DeletionQueue {
    pending: Vec<(u64, DeferredDeletion)>,  // (frame_when_safe, resource)
    current_frame: u64,
    frames_in_flight: u64,  // typically 2-3
}

enum DeferredDeletion {
    Buffer(wgpu::Buffer),
    Texture(wgpu::Texture),
    BindGroup(wgpu::BindGroup),
}

impl DeletionQueue {
    fn enqueue(&mut self, resource: DeferredDeletion) {
        let safe_frame = self.current_frame + self.frames_in_flight;
        self.pending.push((safe_frame, resource));
    }

    /// Call once per frame after presenting
    fn flush(&mut self, completed_frame: u64) {
        self.current_frame = completed_frame;
        // Resources whose safe frame has passed are dropped here
        self.pending.retain(|(safe_frame, _)| *safe_frame > completed_frame);
    }
}
```

**Why deferred deletion:** The GPU may still be reading a resource on frames
already submitted. Deleting immediately causes use-after-free on the GPU.
The deletion queue ensures resources live until all in-flight frames complete.
