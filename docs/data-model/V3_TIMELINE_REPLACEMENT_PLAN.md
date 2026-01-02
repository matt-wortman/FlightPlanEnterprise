# V3 Timeline Replacement Plan (Best-Practice)

## Goal

Replace the current v3 patient timeline chart with the new standalone chart implementation without recoding the existing chart, while preserving backend contracts and rendering all data types immediately (trajectory, annotations, feedbacks, conferences, ECMO). Lock in each step with tests so changes do not regress.

## Scope

- v3 only (Next.js frontend + existing v3 API)
- Replace only the timeline/chart area on the patient detail page
- Keep all other patient page sections unchanged
- Preserve the existing timeline API response shape (`V2TimelineResponse`)

## Source of Truth vs Reference Repo

- **Source of truth (integration):** this repo (FlightPlan v3) is authoritative for the final implementation.
- **Reference-only repo (chart prototype):** `/home/matt/code_projects/claude-timeline/Claude-timeline` is used to pull the tuned chart code, but it is not the integration spec.
- **Rule:** do not implement integration logic in the reference repo. Pull the chart pieces from it and adapt inside this repo.

## Guiding Principles

- Do not change the backend contract.
- Do not rewrite the old chart; replace via adapter + wrapper.
- Use a feature flag to switch between old and new until parity is verified.
- Add tests at each phase to lock in behavior.

## Plan By Phase (with lock-in tests)

### Phase 0 — Confirm categories and baseline

**Work**

- Confirm authoritative v3 callout categories (expected: `oprp`, `cath`, `ae`, `ca`, `image`, `lab`, `other`).
- Audit all annotation `subType` values (API + backend `CLINICAL_NODES`) to ensure category coverage.
- Capture baseline screenshots for the current patient timeline.

**Lock-in tests**

- `frontend`: `npm run type-check`
- Visual baseline snapshot (Playwright or manual screenshot)

---

### Phase 1 — Port the new chart into v3 (no swap)

**Work**

- Pull the standalone chart code from the reference repo (`/home/matt/code_projects/claude-timeline/Claude-timeline`) and copy it into `flightplan-v3/frontend/src/components/timeline-v4/`:
  - Components: `Timeline.tsx`, `FocusChart.tsx`, `ContextChart.tsx`, `SteppedLine.tsx`, `Axes.tsx`, `Callouts.tsx`
  - Hooks: `useTimelineScales.ts`, `useTimeGaps.ts`, `useCalloutHeight.ts`
  - Utils: `calloutLayout.ts`, `discontinuousScale.ts`
- Convert styles from `App.css` into scoped styles (use CSS Modules to avoid global class collisions).
- Add a simple test page to render the new chart with fixture data.

**Lock-in tests**

- `frontend`: `npm run type-check`
- Manual: test page renders, brush works, callouts render

---

### Phase 2 — Align callout types with real v3 categories

**Work**

- Update the new chart’s callout type definitions to use the real v3 categories:
  - `oprp`, `cath`, `ae`, `ca`, `image`, `lab`, `other`
- Add explicit types for non-clinical streams:
  - `feedback`, `conference`
- Update callout color/label mappings accordingly.

**Lock-in tests**

- Unit test: category mapping -> color/label rendering

---

### Phase 3 — Build adapter (real data -> new chart)

**Work**

- Create `timeline-v4/adapter.ts` to convert `V2TimelineResponse` into the new chart data shape:
  - Trajectory segments -> `TimelineEvent[]`
  - Annotations -> `Callout[]`
  - Feedbacks -> `Callout[]`
  - Conferences -> `Callout[]`
  - ECMO -> rendered immediately (see Phase 4)
  - uDays/uDaysPOD -> x-axis day/date/POD rows (parity)
- Add unit tests for all mapping rules.

**Lock-in tests**

- `frontend`: `npm run test` (adapter unit tests)

---

### Phase 3.5 — Legend Drawer integration

**Work**

- Wire the new chart’s controls (gap compression, callout filters, etc.) to the existing `TimelineLegendDrawer` state.
- Remove duplicate UI controls from the new chart when embedded in the patient page.

**Lock-in tests**

- Manual: Legend Drawer toggles affect the new chart as expected.

---

### Phase 4 — ECMO rendering (required immediately)

**Work**

- Phase 4a: Add a minimal ECMO overlay band (functional, not fully styled).
- Phase 4b: Refine ECMO styling to match v3 parity (opacity, label treatment).

**Lock-in tests**

- Unit test: ECMO periods render in SVG
- Visual test on the new test page

---

### Phase 5 — Wire into patient page with feature flag

**Work**

- Create `TimelineV4Wrapper` component that accepts `V2TimelineResponse`.
- Add a feature flag in `patient-detail-client.tsx` to switch old/new timeline.

**Lock-in tests**

- Manual: toggle swaps timeline without layout break
- E2E: patient page loads with new timeline under flag

---

### Phase 6 — Parity and polish

**Work**

- Validate behavior parity (callouts, pinning, time compression, axis labels, colors).
- Adjust chart sizing and CSS to match patient page layout.
- Performance test with dense data (50+ events, 100+ callouts).
- Accessibility pass (keyboard focus, ARIA labels, tooltip text).

**Lock-in tests**

- Playwright screenshot compare
- Manual QA of dense callout scenarios

---

### Phase 7 — Final replace + cleanup

**Work**

- Remove old chart usage on patient page.
- Keep old code only if you want a fallback; otherwise delete to reduce drift.

**Lock-in tests**

- Full frontend test suite
- Final visual regression snapshot

---

## Adapter Mapping Table (Summary)

### Trajectory -> Events

- `V2TrajectorySegment.time[]` + `riskStatusId[]` -> `TimelineEvent.timestamp` + `PatientState`
- `riskStatusId` mapping:
  - 1 -> Discharged
  - 2 -> ACCU
  - 3 -> Extubated
  - 4 -> Intubated
  - 5 -> Procedure
- `segment.name` -> `Location` mapping (heuristic):
  - contains OR/Cath/Procedure -> OR
  - contains ICU/CICU/CTICU -> ICU
  - contains Ward/ACCU/Floor -> Ward
  - contains Home/Discharge -> Home
  - fallback -> Ward

### Annotations -> Callouts

- `subType` -> callout `type` (use v3 categories directly; include all known clinical codes)
- `dbType` fallback if `subType` missing:
  - image -> `image`
  - clinical -> `ca`
  - else -> `other`
- `text` -> title + content (split by newline)

### Feedbacks -> Callouts

- type: `feedback`
- title: `Feedback: {score} / {outcome}`
- content: `performance`, `notes`, `suggestedEdit`

### Conferences -> Callouts

- type: `conference`
- title: `Conference: {type}`
- content: `notes`, `actionItems`

### ECMO

- Render as overlay band on focus chart (best practice).

### uDays / uDaysPOD

- Use `uDays` + `uDaysPOD` to render multi-row x-axis (Day of Week, Date, POD).
- If missing, fall back to derived dates.

---

## Rollback Plan

- Keep old timeline in `components/timeline-legacy/`.
- Feature flag defaults to old timeline in production until sign-off.
- Rollback trigger: visual regression, performance regression, or critical user-reported issues.
- Rollback action: flip feature flag (no code changes required).

---

## Actionable Task List

1. Confirm v3 callout categories + location name mapping rules.
2. Audit all annotation `subType` values (API + backend `CLINICAL_NODES`).
3. Pull chart code from `/home/matt/code_projects/claude-timeline/Claude-timeline` into `flightplan-v3/frontend/src/components/timeline-v4/`.
4. Port styles into CSS Modules (no globals).
5. Add new test page rendering the new chart with fixture data.
6. Update callout type definitions to use v3 categories + `feedback`/`conference`.
7. Build adapter functions in `timeline-v4/adapter.ts`.
8. Write adapter unit tests (riskStatus, location mapping, annotations, feedbacks, conferences, ECMO, uDays/POD).
9. Implement ECMO overlay band in new chart (minimal -> parity).
10. Integrate Legend Drawer controls with the new chart.
11. Add `TimelineV4Wrapper` + feature flag in patient page.
12. Run parity checks (manual + visual) + performance tests.
13. Accessibility sweep (keyboard/ARIA).
14. Remove old chart usage after parity sign-off.
15. Final test run + screenshot baseline update.

## Definition of Done

- New chart renders trajectory + annotations + feedbacks + conferences + ECMO in v3 patient page.
- Real v3 categories are preserved (no placeholder buckets).
- Adapter layer is tested and stable.
- Old chart removed after parity confirmation.
- Visual regression baseline updated.
- Rollback plan documented and tested via feature flag.
- Performance and accessibility checks complete.

---

## Honest Critique (Added 2025-12-30)

### Strengths

1. **Clear phased structure** - Each phase has explicit work items and lock-in tests. This prevents regressions and makes progress measurable.

2. **Guiding principles are sound** - "Don't change the backend contract" and "adapter + wrapper" approach is the right call for a clean replacement.

3. **Feature flag strategy** - Running old and new side-by-side before full swap is best practice for a critical UI component.

4. **Adapter mapping table is detailed** - Having explicit riskStatusId → PatientState mappings documented prevents guesswork.

5. **ECMO explicitly called out** - Recognizing ECMO needs special handling (overlay band) rather than forcing it into callouts shows good analysis.

### Concerns & Gaps

1. **Category list may be incomplete** - Phase 0 lists `oprp`, `cath`, `ae`, `ca`, `image`, `lab`, `other`, but the current codebase has additional clinical codes: `CTO`, `CTP`, `IO`, `MRT`, `NP`, `B`, `PBRF`, `CPBT`, `DCSM`. These need to be accounted for in the mapping.

2. **Feedbacks and Conferences both map to `ca` is problematic** - `ca` means Cardiac Arrest, a critical emergency event. Mapping routine Feedbacks and Conferences to `ca` would give them urgent/alarming styling. They should map to a distinct type like `note` or `other`, or add new types `feedback` and `conference`.

3. **Missing Legend Drawer integration** - The plan doesn't address how the new timeline's controls (gap compression toggle, threshold slider, callout visibility toggles) will integrate with the existing `TimelineLegendDrawer`. This is a significant integration point that needs its own phase or tasks.

4. **Location mapping heuristics are fragile** - Using "contains" string matching (`contains OR/Cath/Procedure -> OR`) could fail on unexpected location names. Should use the existing `LOCATION_COLOR_MAP` from the backend service or create an explicit mapping table with fallback handling.

5. **No mention of callout pinning** - The current timeline has pin/unpin functionality for callouts. Does the new chart support this? If not, is it acceptable to lose this feature, or does it need to be added?

6. **Missing uDays/uDaysPOD handling** - The V2 response includes `uDays[]` (unique days for X-axis) and `uDaysPOD[]` (Post-Operative Day numbers). The plan doesn't mention how these are used in the new chart. The current timeline renders a 3-row X-axis: Day of Week, Date, POD.

7. **ECMO in Phase 4 could block integration** - If ECMO rendering is complex, it could delay the main feature flag rollout (Phase 5). Consider: could Phase 4 be done in parallel, or could ECMO be deferred to a "Phase 4b" after initial integration?

8. **No rollback plan details** - The plan says "keep old code only if you want a fallback" but doesn't specify:
   - Where is the old code archived?
   - How quickly can we revert?
   - What's the rollback trigger criteria?

9. **No performance testing mentioned** - Dense timelines (50+ events, overlapping callouts) could expose performance issues in the new chart. Need to test with realistic dense data, not just happy-path fixtures.

10. **"Scoped styles" is vague** - Phase 1 says "convert styles into scoped styles" but doesn't specify the approach. Options: CSS Modules, Tailwind classes, CSS-in-JS. FlightPlan v3 uses Tailwind—should the new chart adopt Tailwind too, or keep its vanilla CSS in a module?

11. **Missing accessibility considerations** - No mention of keyboard navigation, ARIA labels, or screen reader support for the new chart. Healthcare apps should be accessible.

12. **Test page vs Storybook** - "Simple test page" works, but Storybook would provide better component isolation, prop documentation, and visual testing infrastructure. Worth considering.

### Suggested Additions

1. Add a task to Phase 0: "Audit all annotation `subType` values in the database to confirm complete category list"

2. Add Phase 3.5: "Legend Drawer integration" - Wire gap compression and callout toggles to the new chart

3. Expand the adapter mapping table to include:
   - `uDays` / `uDaysPOD` handling
   - All clinical codes (not just the common ones)
   - Fallback behavior for unknown values

4. Add to Phase 6: "Performance testing with dense timeline (seed a test patient with 50+ events)"

5. Add explicit rollback plan:
   - Archive old timeline in `components/timeline-legacy/`
   - Feature flag defaults to old timeline in production until sign-off
   - Rollback = flip feature flag, no code change needed

### Overall Assessment

This is a **solid plan** that follows good engineering practices (adapter pattern, feature flags, lock-in tests). The main gaps are around edge cases (clinical codes, Legend Drawer integration, pinning) and operational concerns (rollback, performance). Addressing the gaps above would make this production-ready.
