---
name: "figma-implement-design"
description: "Translate Figma nodes into production-ready, adaptive UI with Mock data and named device Preview snapshots. Use when the user provides a Figma URL or node ID, or asks to implement a design that must match Figma specs. Requires a working Figma MCP server connection."
---

# Implement Design

Use this workflow to turn one Figma page or component into project-native UI. The Figma frame is the visual reference, not a fixed-size implementation. Keep the page runnable with Mock data before real business services are ready.

## Prerequisites

- Figma MCP is connected and accessible.
- The user provides a Figma URL with a node ID, or selects a node through `figma-desktop` MCP.
- Read the project's `AGENTS.md`, existing design system, navigation, state, Preview, and resource conventions before editing.
- Follow the current Figma tool protocol and any required prerequisite skills; the tool names below describe the intended operations, not a substitute for capability discovery.
- If the project defines an approved build or Preview tool, follow that rule. Do not substitute another build or Preview tool.

## Required workflow

Follow these steps in order.

### 1. Establish the reference and device matrix

1. Parse the Figma URL into `fileKey` and `nodeId`. For `figma-desktop`, use the selected node.
2. Treat the supplied Figma frame as the reference viewport. Record its width, height, safe-area assumptions, and visible states.
3. Follow the user's explicit device scope. When no scope is specified, suggest a reference device matching the Figma frame, a compact device, and a wider device; choose actual available destinations without requiring a particular model or Pro Max.
4. Record the agreed matrix using the project's available simulator/device names. Keep device labels stable and human-readable; do not use UDIDs as output folder names.

Do not copy the page for each device. Use one adaptive implementation and validate it against the matrix.

### 2. Read the design context

1. Call `get_design_context(fileKey, nodeId)`.
2. Call `get_screenshot(fileKey, nodeId)` and keep the result as the visual reference.
3. If the response is too large, call `get_metadata` first, then fetch the relevant child nodes individually.
4. Record layout constraints, typography, colors, spacing, component variants, image behavior, and interactive states.

### 3. Download and map assets

- Download raster image assets from Figma instead of recreating them locally. Request and keep the `@2x` and `@3x` exports when the Figma MCP or its asset export endpoint supports scale selection. Do not treat a single `1x` download as complete when `@2x` or `@3x` is required by the project.
- Use the exact Figma-exported asset content and preserve a stable project asset name. Do not generate, redraw, upscale, crop, or replace an unavailable image privately.
- Use Figma MCP asset URLs directly when they are provided through `localhost`. If the current MCP connection cannot provide the required `@2x` and `@3x` exports, report the missing export capability instead of silently substituting another image.
- Do not add an icon package when the required asset is already provided by Figma or the project design system.
- Reuse existing project assets and components where they match.
- Do not create placeholder image files, AI-generated images, or privately drawn substitutes. If an image is unavailable, keep the missing asset isolated in the Mock state, record it, and do not mark the asset task complete.

For new iOS asset catalog resources, first confirm the catalog's target membership, existing namespace, asset name, and reference convention. Reuse suitable existing resources without relocating them to enforce this structure. Add actual Figma-exported image files in an image set under a module namespace:

```text
Assets.xcassets/
└── <Module>/                         # Folder with Namespace
    ├── Contents.json                 # properties.provides-namespace: true
    └── <ImageName>.imageset/
        ├── Contents.json             # maps real files to the 2x and 3x scales
        ├── <ImageName>@2x.png
        └── <ImageName>@3x.png
```

If the feature needs a submodule, insert `<Submodule>/` between the module and image set; give it its own `Contents.json` with `properties.provides-namespace` set to `true`. A namespace folder's configuration includes:

```json
{
  "info": { "author": "xcode", "version": 1 },
  "properties": { "provides-namespace": true }
}
```

Use the resulting namespaced reference, such as `<Module>/<ImageName>` or `<Module>/<Submodule>/<ImageName>`, according to the project's convention. Loose PNG files directly inside a namespace folder do not replace an `.imageset`. Create only necessary directories and real resources. Verify the asset reference compiles, then separately verify the image is actually visible in Preview or at runtime; generated resource symbols alone do not establish visibility.

### 4. Build with Mock data first

Implement the page using project-native UI and a local Mock data source or Preview fixture. Keep Mock data behind the same input shape or UseCase protocol that the real implementation will use later.

At minimum, make these states reproducible when the page supports them:

- loading
- content
- empty
- error
- disabled or submitting, when applicable

Do not add network, database, authentication, or unrelated business behavior to finish a visual page. Keep business rules in the existing application layer.

### 5. Apply adaptive layout rules

Use the Figma measurements to derive layout rules rather than copying a single viewport's coordinates.

- Use safe-area-aware containers and the project's layout primitives.
- Prefer flexible container widths, `maxWidth`, grids, stacks, and intrinsic text sizing.
- Classify each dimension as fixed, fluid, or intrinsic before hardcoding it.
- Keep button, toolbar, tile, and image frames stable when their content changes.
- Preserve image aspect ratios and define behavior for unusual aspect ratios.
- Allow text to wrap or scroll where needed; do not truncate solely to fit the reference frame.
- Do not use `UIScreen.main.bounds` as the primary layout strategy.
- Do not solve overflow by blindly clipping content.

After matching the reference device, validate the remaining devices in the agreed matrix. Fix the shared layout rule instead of making a device-specific copy of the View. If an existing page needs a focused compact-screen pass, use `adapt-swiftui-compact-screens` when available.

### 6. Translate to project conventions

- Reuse the project's routing, design tokens, typography, components, state management, and dependency injection.
- Keep business logic out of the View body and do not call concrete network or database services from the View.
- Match the project's MVVM and Clean boundaries when they exist.
- Follow the project's SwiftUI View structure and comment conventions.
- Record any intentional deviation from Figma and the reason.

### 7. Iterate against Figma and the device matrix

Repeat this loop until the page meets the acceptance criteria:

1. Render an agreed device/state Preview, starting with the reference device when it is in scope.
2. Compare it with the Figma screenshot for layout, typography, colors, assets, and interaction states.
3. Render the remaining Previews in the agreed matrix.
4. Check text wrapping, image proportions, safe areas, scrolling, and control overlap.
5. Fix the shared layout or component rule.
6. Re-render all affected devices and states.

Follow the current project's build, Preview, and device tool rules. Confirm each Preview's actual destination. If the tool cannot select the required destination, crashes, or fails to produce a valid result, record that Preview as incomplete; another device's render cannot satisfy it. When permitted native runtime tools are available, continue the affected checks there and label the evidence as runtime rather than Preview. Missing capabilities stop only the affected operation; continue independent implementation and validation work.

### 8. Save Preview snapshots

Store Preview validation screenshots outside `Assets.xcassets` and source code. Unless the project defines another output root, use:

```text
output/preview/
└── <Device>/
    └── <Module>/
        └── <ViewName[-state]>.png
```

Rules:

- Use the device display name for the first folder.
- Use the feature or business module name for the second folder.
- Use the exact code `View` name for the screenshot filename, such as `WelcomeView.png`.
- When one View has multiple states, add only a state suffix, such as `WelcomeView-loading.png` or `WelcomeView-error.png`.
- Keep the same naming scheme across all devices so screenshots can be compared directly.
- Do not put screenshots or placeholder files into `Assets.xcassets`.
- Follow project output conventions first; do not require migration of historical artifacts.

For a visual review or comparison report, use `review-figma-swiftui` when available and join its cumulative `output/ui-review` evidence flow. Do not create a separate `Docs/Preview` report tree or copy the review protocol into this workflow.

## Acceptance checklist

- [ ] Figma context and screenshot were fetched before implementation.
- [ ] Existing project components, tokens, routing, and state conventions were checked.
- [ ] Required raster assets were downloaded from Figma at `@2x` and `@3x` when applicable.
- [ ] New images use `.imageset` directories under module or submodule namespace folders whose `Contents.json` sets `properties.provides-namespace` to `true`; suitable existing resources were reused.
- [ ] Asset target membership and references were checked; compilation and actual Preview or runtime visibility were verified separately.
- [ ] No image was generated, redrawn, upscaled, or used as a private placeholder.
- [ ] The page runs with Mock data without real service dependencies.
- [ ] Required loading, content, empty, error, and interaction states are covered.
- [ ] The actual destinations in the agreed device matrix were rendered and checked; incomplete Previews and any runtime evidence are identified separately.
- [ ] No device-specific copy of the page was created.
- [ ] Text, images, controls, and safe areas do not overlap or overflow.
- [ ] Preview snapshots follow the project output convention, defaulting to `output/preview/<Device>/<Module>/<ViewName[-state]>.png`.
- [ ] Remaining visual deviations and unavailable assets are reported for human review.

## Common issues

### Figma output is truncated

Use `get_metadata` to map the node tree, then fetch only the relevant child nodes with `get_design_context`.

### The reference device matches but another device breaks

Find the fixed frame, screen-bound calculation, missing safe-area handling, or non-wrapping text. Replace it with a shared adaptive rule and re-render the full device matrix.

### The Preview does not match Figma

Compare the Figma screenshot and Preview side by side. Check container geometry first, then typography, spacing, colors, assets, and state-specific content.

### Assets do not load

Verify the Figma MCP asset URL and use the returned `localhost` source without rewriting it. Request the `@2x` and `@3x` exports again if the endpoint supports scale selection. If the asset or required scale is genuinely unavailable, keep the missing-asset state isolated and report it; do not generate a substitute.

### The project has no design system

Use the project's existing primitives and keep new tokens or components local to the Feature until a repeated pattern justifies promotion.
