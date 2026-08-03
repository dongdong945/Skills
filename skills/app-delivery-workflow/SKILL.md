---
name: app-delivery-workflow
description: Use when starting a new app or substantial feature and the goal is to move from requirements and Figma to an isolated, runnable, validated first slice with parallel UI and business work.
---

# App Delivery Workflow

Use this workflow to get a new app or feature running early while keeping UI and business work separable. The workflow coordinates existing skills and project rules; it does not replace the project's architecture, product decisions, or specialist implementation skills.

## 1. Start with project and scope checks

Before editing:

1. Determine whether this is a new app or an existing app.
2. Read the applicable `AGENTS.md`, project README, architecture notes, and nearby implementations.
3. Check Git status, current branch, existing worktrees, and the target project path.
4. Confirm the target platform, minimum supported versions, PRD or feature request, Figma URL/node, and the first runnable scope.
5. If the project is dirty, has unresolved conflicts, or the requested scope overlaps unknown work, stop and report it before creating worktrees.

For an existing app, preserve its conventions. For a new app, create only the minimum App Shell, navigation entry, and feature structure needed to run the first slice.

## 2. Review the requirements before implementation

Use `review-product-requirements` when a PRD, workflow, page list, Figma description, or external contract is available. Confirm:

- core user path and entry point
- pages and navigation
- loading, content, empty, error, disabled, and retry states that matter
- data needed by the UI
- UseCase inputs and outputs when business work is required
- Mock scope and explicit non-goals
- acceptance and verification method

Do not make product decisions for missing core rules. Mark them as blocking or non-blocking questions. Coding begins only after blocking questions are confirmed or explicitly deferred.

## 3. Establish only a lightweight shared agreement

Before parallel work, write down or communicate these items in the task handoff:

- page entry and navigation result
- page state names
- UI input data shape
- UseCase input and output shape, when applicable
- file ownership for UI and business work

Do not introduce a separate contract system, generic architecture base, or broad refactor for this step. Keep the agreement small enough to review by hand.

## 4. Create isolated worktrees and split the work

Create separate branches/worktrees from the same verified base:

```text
UI worktree
- Figma implementation
- Mock data and Preview fixtures
- page layout and interaction
- device adaptation
- Preview snapshots

Business worktree
- Domain models
- UseCases
- Repository protocols and implementations
- data sources, persistence, and business tests
```

Rules:

- Assign file ownership before either worktree edits.
- Do not let both worktrees modify the same ViewModel, router, design-system component, asset directory, or project file.
- Freeze the lightweight shared agreement while parallel work is in progress. Changes to it require a separate, explicit handoff.
- Use the project's existing branch and commit conventions. Keep each task small enough for manual review.

## 5. Run the UI work

Use `figma-implement-design` for each independent page or UI task. The UI work must:

- fetch Figma context and screenshot before implementation
- use Mock data behind the expected input or UseCase shape
- cover the required page states
- validate the Figma reference device plus compact and wide devices
- download real Figma assets at the required scales
- place assets under the project's module or submodule namespace rules
- never generate private image substitutes or placeholder image files
- save Preview snapshots using the project's agreed device/module/View naming

Do not wait for real networking or database code before proving the page flow.

## 6. Run the business work

Use the existing project architecture and MVVM/Clean conventions when implementing business behavior:

- keep business rules in the application/domain layers
- expose explicit UseCase or service interfaces to Presentation
- keep Repository protocols separate from concrete data sources
- make loading, error, retry, and empty behavior explicit
- add focused tests for business rules and boundaries

Do not change the UI layout or add production-only behavior just to make a business task easier to implement.

## 7. Integrate in one place

After the UI and business tasks have independently completed their small commits, integrate them in the coordinating worktree or branch:

1. Verify the two branches still share the expected base and inspect their diffs.
2. Integrate business interfaces and implementations first when the UI already uses the agreed protocol.
3. Replace UI Mock dependencies through the composition root or project dependency container.
4. Resolve only integration conflicts; do not hide unrelated refactors in this step.
5. Recheck navigation, state mapping, assets, and project-file changes.

If the merge requires changing the shared agreement or crossing file ownership, stop and report the conflict instead of forcing a resolution.

## 8. Validate the first runnable slice

Use the project's approved validation tools and `AGENTS.md` rules. At minimum, verify:

- the app starts or the target feature can be entered
- the core path navigates correctly
- Mock or real dependencies produce the expected states
- compact and wide device layouts do not overlap or overflow
- Preview snapshots are present and named consistently
- focused tests or static checks cover the changed business behavior
- remaining visual deviations and unverified runtime behavior are recorded

Keep build success, Preview success, tests, simulator interaction, and real-device validation as separate evidence. Do not claim a stronger result than the tool actually verified.

## 9. Review, commit, and hand off

For each task:

1. Review the task diff and fix findings.
2. Run the narrowest relevant validation.
3. Commit only task-related files using the project's commit convention.
4. Report the branch, commit, changed scope, verification results, and remaining risks.

Do not push unless the user requests it. Do not include unrelated staged or working-tree changes.

## Delivery result

The first slice is ready when:

- the app can start
- the main pages and core navigation exist
- the UI runs with Mock data before real services are complete
- required state paths are visible and testable
- the business layer has explicit integration points
- UI has been checked on the reference, compact, and wide devices
- the remaining visual polish is isolated as a human review item

## Stop conditions

Stop and report instead of continuing when:

- a core product rule or data contract is unresolved
- the base worktree contains conflicts or unclear user changes
- Figma MCP or required project tools are unavailable
- UI and business changes require the same files without an agreed owner
- the requested integration would require an unapproved architecture refactor
