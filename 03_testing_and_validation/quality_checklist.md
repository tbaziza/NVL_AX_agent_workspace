---
title: "Quality Checklist — Pre-Handoff Validation"
module: 03_testing_and_validation
tags: [quality, checklist, validation, handoff, doa]
---

# Quality Checklist — Pre-Handoff Validation

## Build Verification

- [ ] All 19 shadow files present: `ls .shadow/ | wc -l` = 19
- [ ] `fix_zse5_libs.sh` ran successfully (100+ symlinks, 352 RPATH patches)
- [ ] `ldd zse_engine.so | grep "not found"` returns empty
- [ ] `readmem.dump` is a regular file (not symlink) with absolute paths
- [ ] U0-U3 directories exist in `backend_default/`
- [ ] MuDb `equis/info` file is non-empty

## Test Verification

- [ ] `spacedoa_mobile`: PASSED
- [ ] `spacex_mobile`: PASSED
- [ ] Zero assertion failures in both tests
- [ ] `iosf_sb_jem_tracker` either passes or is in `not_fail_on` list
- [ ] `postmortem.log` shows `OVERALL STATUS: PASS` for both tests

## Documentation Verification

- [ ] All bugs encountered during this integration are documented in `known_bugs_and_fixes/`
- [ ] `commands_reference.md` is up-to-date with any new commands used
- [ ] `common_patterns.md` updated if new patterns discovered
- [ ] Build session log appended to `build_flow.md`
