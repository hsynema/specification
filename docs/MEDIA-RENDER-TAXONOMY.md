# MEDIA render taxonomy — the layered design

The governing rule, stated once: **generative models produce into editable
representations; a deterministic renderer — never the generative model — holds final
authority over pixels.** Everything below is placed by that rule, and every artifact at
every layer writes the provenance ledger, so the chain from prompt to pixel stays
walkable. The two axes that place a system here: *representation* (mesh ↔ volume ↔
points/Gaussians ↔ implicit ↔ pixels) and *controllability* (procedural → conditioned →
free-form).

Status vocabulary — honest, four words: **SHIPPED** (runs today in the MEDIA tab),
**KERNELS-PRESENT** (the compute exists in NativeDAWN, the bridge does not),
**CANDIDATE** (identified runtime, not installed), **HOOK** (interface reserved, nothing
behind it). `Media/RenderGraph.swift` is this table as types; its `availability()` is
the code answering for itself.

## I · Physically-based light transport — the substrate

| Piece | Where | Status |
|---|---|---|
| Real-time raster (deferred-class) | SceneKit viewport, `ViewportScene` + light rigs | SHIPPED |
| Unidirectional MC path tracing | NativeDAWN `LightTransportMonteCarlo.metal` — `lt1_monte_carlo`, `lt1_clear_accumulation`, `lt1_prepare_capture` | KERNELS-PRESENT |
| ReSTIR-class reservoir transport | NativeDAWN `VolumetricReSTIR.metal` — `lt2_restir_pass`, `lt2_clear_reservoirs` | KERNELS-PRESENT |
| Hardware ray intersection | NativeDAWN `RaytracingKernels.metal` — `dawn_rt_kernel` | KERNELS-PRESENT |
| Spectral / polarized / BDPT / photon mapping | — | HOOK |

The bridge (the one build that unlocks the row): a `SubstrateRenderer` conformance that
compiles the NativeDAWN `.metal` sources (MetalEngines already owns a device; the
abraxas `metal_compile_kernels` path is the fallback), feeds it the viewport's scene as
buffers (meshes via the GLB loader's raw geometry; `meshoptimizer` is vendored in
NativeDAWN for index/vertex-cache preparation), accumulates progressively, and hands
the result back as the HERO mode of the viewport and the high branch of the turntable
recorder. The raster viewport remains the working view; HERO is the final-pixel view.

## II · Differentiable & inverse rendering — the bridge layer

All HOOK today. The honest local route when wanted: MLX autodiff over a soft
rasterizer for silhouette/appearance fitting (material capture against Object Capture
photo sets is the first real use). Depth Pro and Cubify (below) are the perception
priors this layer would consume.

## III · Neural scene representations

| Piece | Where | Status |
|---|---|---|
| Mesh + PBR textures | GLB/USDZ library + viewport | SHIPPED |
| Gaussian splatting (3DGS) | `.ply/.splat` — Metal splat rasterizer as a `SubstrateRenderer` | CANDIDATE (production favorite; splat files preview as point clouds first) |
| NeRF family / implicit SDF | — | HOOK (SDF route matters when watertight engineering meshes are the ask) |

## IV · Generative 3D

| Piece | Where | Status |
|---|---|---|
| 3D-native latent flow → mesh+PBR | TRELLIS.2 (SLat flow, 512→1536 tiers) + Vision cutout | SHIPPED |
| Multi-view reconstruction | Apple Object Capture (photos → USDZ) | SHIPPED |
| Procedural / parametric | GBC graphs are the seed; grammar→geometry generator emitting into the library with seeds in provenance | HOOK (the deterministic, contract-grade branch) |
| Score distillation, LRM-class feed-forward, autoregressive mesh (MeshGPT-class) | — | CANDIDATE/HOOK per model availability on MLX |
| 3D perception priors | Cubify Anything (boxes), Depth Pro (metric depth) | CANDIDATE (researched; MPS-untested) |

## V · Generative video

| Piece | Where | Status |
|---|---|---|
| Spacetime DiT / rectified flow | LTX-2.5 MLX — the deck's engine | SHIPPED |
| Conditioned v2v (anchor conditioning) | frame anchors, FRAME→3D, per-clip pins | SHIPPED |
| Assembly authority | AVFoundation composed cut — dissolve ramps, audio mix; the deterministic layer owning delivered pixels | SHIPPED |
| Interpolation / video SR (FILM/RIFE-class, latent upscalers) | — | CANDIDATE (MetalFX spatial/temporal is the platform-native first step) |
| Interactive world models | — | HOOK (the one branch where the substrate/generative separation collapses; keep it quarantined from the delivery path) |

## VI · Neural components inside the pipeline — the hybrid layer that ships

| Piece | Where | Status |
|---|---|---|
| Learned upscaling | MetalFX (`MTLFXSpatialScaler`/temporal) in the turntable + assembly path | CANDIDATE (platform API present; wire = render→texture→scale→writer) |
| Denoising for the PT substrate | MPS SVGF-class denoiser after `lt1` accumulation | CANDIDATE (pairs with the KERNELS-PRESENT bridge) |
| Neural path guiding / radiance caching | — | HOOK |

## The contract, restated as wiring

```
prompt ──LTX──▶ pixels (clips) ──deterministic assembly──▶ delivered cut
image ──TRELLIS/Capture──▶ mesh+PBR ──raster (work) / lt1+ReSTIR (hero)──▶ pixels
graph ──GBC/procedural──▶ parametric geometry ──same substrates──▶ pixels
        every arrow appends provenance · every artifact packable into .syn
```

Editing lives on representations (the deck's params, the viewport's rig, the mesh
exports); substrates render them; generative models are suppliers, not authorities.
When a world-model branch arrives, it gets its own lane and its outputs enter the
library like any supplier — the ledger keeps it honest.
