---
status: resolved
trigger: "okay see previously in pass 1.5 we used to run a script for doing the timeline and everything. it used to try and figure out the timeline of each user. there was method that combined python with llmm but now it just dumps everything to the llm. I.. don't like that style. can you take a look at why this is happening?"
created: "2026-07-02T09:36:00+03:00"
updated: "2026-07-02T09:36:00+03:00"
---

# Symptoms
- **Expected behavior**: Pass 1.5 should use the hybrid Python+LLM timeline logic (`_interpolate_dates` and `_map_aliases`).
- **Actual behavior**: Pass 1.5 dumps everything to the LLM via `_run_cleaning_pass`.
- **Error messages**: N/A
- **Timeline**: Changed recently in commit `20e9ef9` (feat: dynamically run cleaning pass from config).
- **Reproduction**: Run the pipeline.

# Current Focus
- **next_action**: implement fix
- **hypothesis**: The hardcoded hybrid Python+LLM timeline logic was replaced by a purely config-driven `_run_cleaning_pass` in commit `20e9ef9`. If config strategy is "llm", it bypasses the old logic.
- **test**: N/A
- **expecting**: 

# Evidence
- timestamp: 2026-07-02T09:36:00+03:00
  note: Initial symptoms gathered. Confirmed via git log that commit 20e9ef9 replaced `_interpolate_dates` and `_map_aliases` calls with `_run_cleaning_pass`.

# Eliminated
- The old logic was completely deleted. (False, `_interpolate_dates` and `_map_aliases` still exist in `pipeline.py`).

# Resolution
- **root_cause**: Commit `20e9ef9` introduced a dynamic `_run_cleaning_pass` based on configuration, overwriting the hardcoded calls to `_interpolate_dates` and `_map_aliases` in Pass 1.5. Since the default config uses the `llm` strategy, it defaults to purely dumping pages to the LLM.
- **fix**: Add a `hybrid` strategy option in `ConfigCleaning` that invokes the original `_interpolate_dates` and `_map_aliases` methods in `pipeline.py`.
