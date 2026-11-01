# Project management

VirtueMotif uses GitHub Issues and Projects to make work discoverable, prioritized, and verifiable. The project board is the working view; issues and pull requests remain the source of truth for scope, discussion, and implementation.

## Board purpose

**Project name:** VirtueMotif — Engineering Roadmap

**Description:** Plan and deliver trustworthy, reproducible, production-quality audio-reactive lyric video tooling. Track improvements from triage through implementation, review, and verified release.

The board should be useful to both maintainers and first-time contributors. Every active card should answer: what problem is being solved, why it matters, what done means, and how it will be verified.

## Workflow

Use the built-in **Status** field with these options, in this order:

1. **Inbox** — newly captured work that has not been triaged.
2. **Ready** — accepted, scoped, and actionable work.
3. **In progress** — actively being implemented.
4. **In review** — awaiting code review or required validation.
5. **Done** — acceptance criteria met and changes merged or otherwise completed.

Keep deferred or rejected work out of the active workflow: close it with a clear explanation or retain it in the backlog with a documented reason. Do not mark work Done merely because a PR was opened.

## Fields

Keep the board scannable. Use GitHub's built-in fields wherever possible, and add only the custom fields that help make decisions.

| Field | Type | Guidance |
| --- | --- | --- |
| Status | Single select | The workflow above; use as the board's grouping field |
| Priority | Single select | P0 — critical; P1 — high; P2 — normal; P3 — opportunistic |
| Area | Single select | Python pipeline; Remotion; Audio/timing; Effects/rendering; Docs; CI/security; Release |
| Estimate | Number | Optional, coarse effort estimate; do not confuse with a commitment |
| Target date | Date | Optional; set only when there is a real delivery target |
| Assignees | Built-in | One directly responsible owner for active work |
| Labels | Built-in | Apply a small, consistent vocabulary from the repository |

Avoid adding fields that duplicate labels, issue titles, or the built-in Status/Assignees metadata.

## Saved views

Create these views in this order:

### 1. Delivery board — Board layout

- Group by **Status**.
- Show Priority, Area, Assignees, and Labels on cards.
- Sort items within each status by Priority, then oldest-created first.
- Use as the default view for day-to-day work.

### 2. Triage inbox — Table layout

- Filter: `status:Inbox is:open` (adapt the filter to the exact status option name shown in the UI).
- Show Title, Priority, Area, Labels, Created, and Assignees.
- Sort oldest first so unattended issues do not disappear.

### 3. Priority backlog — Table layout

- Include open items not in Done.
- Show Priority, Status, Area, Assignees, and Estimate.
- Sort by Priority, then oldest-created first.
- Use this view to choose the next Ready item.

### 4. Roadmap — Roadmap layout

- Use Start date and Target date if both are maintained; otherwise use Target date and do not invent start dates.
- Group by Area or milestone where useful.
- Keep dates realistic and maintained. An undated issue belongs in the backlog, not at an arbitrary position on a timeline.

### 5. Contributor opportunities — Table layout

- Filter to open items labelled `good first issue` or `help wanted`.
- Show Area, Priority, and Assignees.
- Each item must contain enough context and acceptance criteria for a contributor to make progress independently.

### 6. Recently completed — Table layout

- Filter to closed items or Status Done.
- Sort by most recently updated.
- Use for release-note preparation and progress reviews.

## Labels

Use labels to describe the nature of work, not to duplicate status.

### Type

- `bug` — incorrect or unexpectedly failing behavior.
- `enhancement` — user-visible capability improvement.
- `documentation` — documentation or examples.
- `maintenance` — refactoring, dependency upkeep, and repository hygiene.
- `security` — security-sensitive work; follow the private reporting process for vulnerabilities.

### Area

- `area:python`
- `area:remotion`
- `area:audio-timing`
- `area:effects-rendering`
- `area:ci`
- `area:docs`
- `area:release`

### Priority

- `priority:P0` — blocks safe operation or a critical workflow.
- `priority:P1` — high-impact work for the next delivery cycle.
- `priority:P2` — normal planned work.
- `priority:P3` — useful but non-urgent.

### Contribution

- `good first issue`
- `help wanted`

Prefer the board's Priority and Area fields for sorting and grouping. Use matching labels for repository-wide issue searches and automation; avoid inconsistent duplicate vocabularies.

## Automation

Configure these built-in workflows in the Project's **Workflows** settings:

- **Auto-add to project:** add newly opened issues and pull requests from `virtuewise/virtuemotif`. Keep new items in Inbox until triaged.
- **Item closed:** move closed issues to Done.
- **Pull request merged:** move merged PRs to Done.
- **Item reopened:** return reopened work to Inbox or Ready for explicit triage.

If the UI offers a default status when items are added, choose **Inbox**. Do not auto-close linked issues unless the team has confirmed the repository's closing-keyword conventions and the workflow is predictable.

## Issue quality standard

Every substantial issue should include:

- **Context:** what is happening today and who or what it affects.
- **Goal:** the desired outcome, without prematurely prescribing implementation.
- **Acceptance criteria:** observable conditions that determine completion.
- **Validation:** tests, commands, metrics, screenshots, or manual checks that will demonstrate correctness.
- **Scope and guardrails:** compatibility, data/asset rights, performance, or security constraints where relevant.
- **Dependencies:** related issues or blockers, when applicable.

Keep issues focused enough that one PR can usually complete them. Split large work into linked issues with a clear parent objective. Use checklists for verifiable steps, not as a substitute for acceptance criteria.

## Pull request and completion policy

- Link PRs to their tracking issue and explain the user or engineering impact.
- Run the relevant Python and/or Remotion checks before requesting review.
- Include evidence for user-visible changes where practical.
- Record material trade-offs and follow-up work explicitly.
- Move work to Done only after required checks pass and the implementation is merged or the completion condition is otherwise met.
- Close superseded or duplicate issues with a short explanation and a link to the canonical item.

## Roadmap priorities

Use the following sequence as a default, revisiting it when evidence changes:

1. **Trust and release hygiene:** resolve repository metadata inconsistencies, document asset provenance, and verify security settings.
2. **Reliability:** strengthen deterministic tests around configuration, audio/timing, frame output, and FFmpeg failure handling.
3. **Reproducibility:** align runtime/dependency guidance with CI and keep test fixtures small, licensed, and repeatable.
4. **Rendering quality:** measure render correctness, performance, and audio/video synchronization before optimizing.
5. **Architecture and contributor experience:** document stable interfaces, add decision records when useful, and make contribution tasks approachable.

This is a prioritization guide, not a promise of dates. Create target dates only after scope, dependencies, and capacity are understood.

## Initial setup checklist

- [ ] Create or rename the GitHub Project to **VirtueMotif — Engineering Roadmap** and apply the description above.
- [ ] Configure Status options in the stated order and set Inbox as the default for new items.
- [ ] Add Priority, Area, Estimate, and Target date fields.
- [ ] Create the six saved views in the stated order, with Delivery board as the default.
- [ ] Configure auto-add and item lifecycle workflows.
- [ ] Add all currently open repository issues and pull requests; triage each to an accurate status, priority, and area.
- [ ] Confirm the board has no stale duplicate cards and no completed work incorrectly left active.
- [ ] Review the board from a logged-out/public perspective to ensure its name, description, and visible content make sense to outside contributors.

GitHub's Project settings and saved views are configured in the web UI. Keep this document as the repository's source-controlled specification so future board changes remain intentional and reviewable.
