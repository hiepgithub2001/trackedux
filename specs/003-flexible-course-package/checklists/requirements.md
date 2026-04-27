# Specification Quality Checklist: Flexible Course Package with Class Catalog & Lesson Kind Vocabulary

**Purpose**: Validate specification completeness and quality before proceeding to planning
**Created**: 2026-04-27
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No implementation details (languages, frameworks, APIs)
- [x] Focused on user value and business needs
- [x] Written for non-technical stakeholders
- [x] All mandatory sections completed

## Requirement Completeness

- [x] No [NEEDS CLARIFICATION] markers remain
- [x] Requirements are testable and unambiguous
- [x] Success criteria are measurable
- [x] Success criteria are technology-agnostic (no implementation details)
- [x] All acceptance scenarios are defined
- [x] Edge cases are identified
- [x] Scope is clearly bounded
- [x] Dependencies and assumptions identified

## Feature Readiness

- [x] All functional requirements have clear acceptance criteria
- [x] User scenarios cover primary flows
- [x] Feature meets measurable outcomes defined in Success Criteria
- [x] No implementation details leak into specification

## Notes

- Ten clarifications resolved on 2026-04-27 across three `/speckit-clarify` invocations. Outcomes:
  - Q1 (skill_level unification): drop the structured `skill_level` field on Student; use the existing free-text notes field with a placeholder hint.
  - Q2 (migration default for legacy packages): no migration — drop and rebuild the course package data store.
  - Q3 (active-package editability): active packages are immutable; corrections via deactivate + reissue.
  - Q4 (existing-vs-new lesson kind on package form): typeahead/combobox with inline create — admin can pick a suggestion or type a brand-new name.
  - Q5 (lesson kind lifecycle): no lifecycle management — Lesson Kinds is a passive append-only vocabulary; no rename/deactivate/reactivate/delete UI; no active/inactive state. Removed the dedicated "Lesson Kinds management screen" story.
  - Q6 (Classes tab + class IDs): added a "Classes" navigation tab; class display ID = `{TeacherFirstName}-{Weekday3}-{HHMM}[-{N}]`, derived from current values, with a sequential disambiguator suffix; references between entities use the stable UUID.
  - Q7 (class price): added `tuition_fee_per_lesson` (positive integer VND, ceiling 100,000,000) on Class; admin-only.
  - Q8 (package → class FK): every course package MUST reference exactly one class by stable UUID; class is required on the package form.
  - Q9 (package fee derivation): auto-populate from `class.tuition_fee_per_lesson × number_of_lessons`; admin can override; manual edits preserved across subsequent class/lesson-count changes.
  - Q10 (student-class enrollment): validate, don't auto-enroll. Package save is rejected if the student isn't already enrolled in the chosen class; admin must enroll first via the existing spec 001 flow.
- All checklist items now pass. Spec is ready for `/speckit-plan`.
