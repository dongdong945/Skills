---
name: app-delivery-workflow
description: Use when starting a new app or substantial feature and the goal is to move from requirements and Figma to an isolated, runnable, validated first slice with fixed UI, business, and integration worktrees.
---

# App Delivery Workflow

Use this workflow to get a new app or substantial feature running early while keeping UI and business work separable. The workflow coordinates existing skills and project rules; it does not replace the project's architecture, product decisions, or specialist implementation skills.

The root agent is the delivery coordinator. Delegate UI implementation to the `ui-implementer` custom agent and business implementation to the `business-implementer` custom agent. Both agents must use `gpt-5.6-sol` with `high` reasoning and must not recursively create more agents. Use `delivery-acceptance` as the read-only final review procedure instead of creating another implementation agent. If either custom agent or isolated worktree support is unavailable, stop and report it rather than silently substituting a general-purpose agent or writing both scopes in one checkout.

This workflow is platform-neutral. Use the project's platform-specific skills and `AGENTS.md` rules for scaffolding, UI implementation, build, Preview, tests, and simulator/device validation.

## Delivery gates

Do not start parallel implementation until the following are known or explicitly deferred:

- target project and base branch/commit
- first runnable user path and its entry point
- requirements, non-goals, and unresolved product decisions
- Figma URL/node or an explicit UI-only omission
- UI states and the data shape needed to render them
- business contract, when real business behavior is in scope
- device matrix and validation tools

An unresolved core rule, missing external contract, unavailable required tool, or unclear file owner is a stop condition, not an implementation detail to guess.

## 1. Start with project and scope checks

Before editing:

1. Determine whether this is a new app or an existing app.
2. Read the applicable `AGENTS.md`, project README, architecture notes, and nearby implementations.
3. Resolve the main project root, then check Git status, current branch, existing worktrees, branch name collisions, and the target project path.
4. If the project is dirty, has unresolved conflicts, or the requested scope overlaps unknown work, stop and report it before changing `.gitignore` or creating worktrees.
5. Ensure the project-root `.gitignore` contains the exact root-relative rule `/.worktrees/`. If it is missing, add it as a small setup task, self-review it, and commit it before creating any worktree.
6. Confirm the target platform, minimum supported versions, PRD or feature request, Figma URL/node, and the first runnable scope.
7. Record the resulting base commit used by every worktree. Do not create one worktree from another worktree's uncommitted state.

For an existing app, preserve its conventions. For a new app, first create only the minimum App Shell, navigation entry, and feature structure needed to run the first slice. Verify that shell before splitting UI and business work.

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
- loading, empty, error, retry, and completion behavior that both sides must represent
- file ownership for UI and business work

Do not introduce a separate contract system, generic architecture base, or broad refactor for this step. Keep the agreement small enough to review by hand.

## 4. Assign runtime roles and create isolated worktrees

Confirm that `ui-implementer` and `business-implementer` are installed with `model = "gpt-5.6-sol"` and `model_reasoning_effort = "high"`. Use these responsibilities when delegating:

```text
Root coordinator
- confirms inputs and gates
- owns the shared agreement and integration worktree
- reviews specialist results and decides whether to continue

ui-implementer
- owns Figma translation, Views, UI-only components, Mock/Preview fixtures,
  UI assets, adaptive layout, and named Preview snapshots

business-implementer
- owns Domain, Data, UseCases, Repositories, DataSources, ViewModels,
  dependency wiring, routing, migrations, and focused business tests

Acceptance reviewer
- uses `delivery-acceptance` as the read-only final acceptance procedure
- reads the final diff and evidence
- does not edit implementation files
- reports missing states, ownership violations, merge risks, and unverified claims
```

The two implementation agents must receive the same base commit and lightweight agreement. Each handoff must include the assigned worktree path, branch, one reviewable task, owned files, forbidden files, acceptance criteria, and approved validation tools. The agents operate only inside their assigned worktrees; they do not create, rename, switch, or remove worktrees.

Create separate branches/worktrees from the same verified base under the main project root:

```text
<ProjectRoot>/.worktrees/
├── ui-implementer/
├── business-implementer/
└── integration/
```

The directory names are fixed. Branch names remain feature-specific and follow the target project's Git conventions. A fixed path supports one active delivery flow per project at a time.

Rules:

- The root coordinator exclusively creates and manages the three worktrees.
- Do not create suffixed or temporary alternatives such as `ui-implementer-2`, `business-implementer-temp`, or `integration-new`.
- Before creation, compare the fixed paths with `git worktree list --porcelain`. If a path exists but is not a registered worktree, stop. If it is registered with a different branch, base, or delivery task, stop.
- If an existing fixed worktree contains uncommitted changes or unmerged task commits, preserve it and stop; do not clean, reset, reuse, or delete it automatically.
- Assign file ownership before either worktree edits.
- The business worktree owns ViewModels, routing, dependency wiring, migrations, and project/build configuration unless the handoff explicitly assigns one of them elsewhere.
- The UI worktree owns Views, UI-only components, Mock/Preview fixtures, Figma-exported assets, and Preview output.
- Do not let both worktrees modify the same ViewModel, router, design-system component, asset directory, or project file.
- If a platform project requires a shared project manifest or generated group file, assign that file to one owner before work starts; the other worktree adds source files without editing it.
- Freeze the lightweight shared agreement while parallel work is in progress. Changes to it require a separate, explicit handoff.
- Use the project's existing branch and commit conventions. Keep each task small enough for manual review.
- If Git worktrees are unavailable, do not simulate parallel writes in one checkout.

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

The UI must remain runnable with Mock data through the same input shape or UseCase protocol expected after integration. Do not wait for real networking or database code before proving the page flow.

For iOS/SwiftUI projects, follow `figma-implement-design` for the reference, compact, and wide device matrix and store snapshots under the device/module/View naming scheme (for example `Docs/Preview/<Device>/<Module>/<ViewName>.png`). Do not copy the View for each device. Keep unavailable assets isolated and reported for human follow-up.

## 6. Run the business work

Use the existing project architecture and MVVM/Clean conventions when implementing business behavior:

- keep business rules in the application/domain layers
- expose explicit UseCase or service interfaces to Presentation
- keep Repository protocols separate from concrete data sources
- make loading, error, retry, and empty behavior explicit
- add focused tests for business rules and boundaries
- keep the agreed UI input and UseCase contract stable; if it must change, pause and update both workstreams before continuing

Do not change the UI layout or add production-only behavior just to make a business task easier to implement.

## 7. Integrate in one place

After the UI and business tasks have independently completed their small commits, integrate them only in `<ProjectRoot>/.worktrees/integration`. Do not merge uncommitted work:

1. Verify the two branches still share the expected base and inspect their diffs.
2. Integrate business interfaces and implementations first when the UI already uses the agreed protocol.
3. Replace UI Mock dependencies through the composition root or project dependency container.
4. Resolve only integration conflicts; do not hide unrelated refactors in this step.
5. Recheck navigation, state mapping, assets, and project-file changes.

If the merge requires changing the shared agreement or crossing file ownership, stop and report the conflict instead of forcing a resolution. Preserve both branches until the integration diff and validation are accepted.

Do not remove fixed worktrees automatically after delivery. When cleanup is explicitly requested, first verify cleanliness, merged ancestry, and the registered paths, then use `git worktree remove`; never recursively delete `.worktrees/`.

## 8. Validate the first runnable slice

Use `delivery-acceptance` for the read-only final review. Follow the project's approved validation tools and `AGENTS.md` rules. At minimum, verify:

- the app starts or the target feature can be entered
- the core path navigates correctly
- Mock or real dependencies produce the expected states
- compact and wide device layouts do not overlap or overflow
- Preview snapshots are present and named consistently
- focused tests or static checks cover the changed business behavior
- remaining visual deviations and unverified runtime behavior are recorded

Keep build success, Preview success, tests, simulator interaction, and real-device validation as separate evidence. Do not claim a stronger result than the tool actually verified.

The acceptance reviewer must check the final first slice against the shared agreement, especially:

- navigation entry and return result
- state mapping between View, ViewModel, and UseCase
- Mock-to-real dependency replacement point
- device adaptation, safe areas, text wrapping, image behavior, and Preview naming
- changed files versus the ownership map
- merge conflicts, unrelated changes, and missing validation evidence

## 9. Review, commit, and hand off

For each task:

1. Review the task diff and fix findings.
2. Run the narrowest relevant validation.
3. Commit only task-related files using the project's commit convention.
4. Report the branch, commit, changed scope, verification results, and remaining risks.

Do not push unless the user requests it. Do not include unrelated staged or working-tree changes.

Leave detailed UI polish, copy refinement, and known Figma deviations as explicit human-review items after the first runnable slice is validated. Do not present those items as business or integration failures.

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
- `ui-implementer` or `business-implementer` is missing or not configured for `gpt-5.6-sol` with `high` reasoning
- the project-root `.gitignore` does not contain `/.worktrees/` and cannot be committed safely
- a fixed worktree path is unregistered, dirty, attached to another task, or based on an unexpected commit
- Figma MCP or required project tools are unavailable
- UI and business changes require the same files without an agreed owner
- the requested integration would require an unapproved architecture refactor
