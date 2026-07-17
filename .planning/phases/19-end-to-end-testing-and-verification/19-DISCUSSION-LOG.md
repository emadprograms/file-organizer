# Phase 19 Discussion Log

## Topic: Test Suite Structure & Naming
- **Options presented:** Group by feature/module vs Keep flat with strict naming
- **User selection:** Keep them flat in `tests/` but enforce a strict `test_[module].py` naming convention.

## Topic: Golden Dataset Input/Output Validation
- **Options presented:** Rename + explicit output vs Rename + golden directory
- **User selection:** keep the name golden_1273 and the folder structure of the input 1273 file and the output 1273 file must be very clear inside it.

## Topic: .source_files Directory Placement
- **Options presented:** Place exactly inside target house folder natively vs copy dynamically
- **User selection:** Yes, `.source_files` must be placed exactly inside the target house folder (e.g. `golden_1273/input/1273/.source_files/`) so the code finds it natively.

## Topic: Dry Run and E2E Routing Testing
- **Options presented:** Require state files in input vs mock LLM responses
- **User selection:** we should use the jsons AND mock the llm responses at function level to create the files in that manner. If you want, you can even run the code once. see the llm responses and save it and use it later to mock them exactly.
