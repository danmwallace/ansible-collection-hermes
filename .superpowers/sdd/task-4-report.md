# Task 4 Completion Report — Hermes Image Tag Pinning

**Status:** DONE

## Summary

Successfully pinned image tags in the danmwallace/hermes collection and bumped the version from 1.2.4 to 1.2.5.

## Changes Applied

### 1. Pinned hermes image tag
**File:** `roles/hermes/defaults/main.yml`
- Changed: `hermes_image_tag: latest` → `hermes_image_tag: v2026.7.1`
- Line 6

### 2. Pinned hermes_gateway image tag
**File:** `roles/hermes_gateway/defaults/main.yml`
- Changed: `hermes_gateway_image_tag: latest # noqa: var-naming[no-role-prefix]` → `hermes_gateway_image_tag: v2026.7.1 # noqa: var-naming[no-role-prefix]`
- Line 37 (preserved inline noqa comment)

### 3. Bumped collection version
**File:** `galaxy.yml`
- Changed: `version: 1.2.4` → `version: 1.2.5`
- Line 4

### 4. Added CHANGELOG entry
**File:** `CHANGELOG.md`
- Inserted new section: `## [1.2.5] - 2026-07-02`
- Documented changes: pinning of hermes and hermes_gateway image tags to v2026.7.1
- Inserted after file header (no Unreleased section existed)

## Verification

**ansible-lint result:** ✅ Passed
- 0 failures, 0 warnings
- Production profile validation successful
- 42 files processed

## Commit Details

- **SHA:** 469929a
- **Message:** `chore: release 1.2.5 — pin hermes image tags to v2026.7.1`
- **Files committed:** 4 (roles/hermes/defaults/main.yml, roles/hermes_gateway/defaults/main.yml, galaxy.yml, CHANGELOG.md)

## Notes

- All changes follow the exact specifications from task-4-brief.md
- The hermes_gateway_image_tag line preserved its existing noqa comment as required
- Date-based versioning (v2026.7.1) correctly applied to both container image tags
- No linting issues detected after modifications
