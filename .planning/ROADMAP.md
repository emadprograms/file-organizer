# Roadmap

## Phase 1: Configuration Infrastructure

**Goal**: Build the core capability to parse and validate user-provided YAML/JSON configuration files.
**Requirements**: CONF-01, CONF-02, CONF-03
**Success Criteria**:

1. Tool can read and parse a user-provided `config.yaml` or `config.json`.
2. A valid `sample-config.yaml` replicating the existing hardcoded tenant logic is provided.
3. Private test configuration works seamlessly for regression testing.

## Phase 2: Pipeline Adaptation (Extraction & Cleaning)

**Goal**: Generalize the first half of the pipeline (Passes 1 and 1.5) to use the new config-driven instructions instead of hardcoded rules.
**Requirements**: EXT-01, EXT-02
**Plans:** 2/2 plans complete
**Success Criteria**:

1. Pass 1 extracts metadata based exclusively on instructions from the configuration file.
2. Pass 1.5 executes cleaning and interpolation logic dynamically based on config rules.

Plans:

- [x] 02-01-PLAN.md — Extract metadata dynamically based on config
- [x] 02-02-PLAN.md — Refactor Pass 1.5 to use configured cleaning rules

## Phase 3: Organization Logic (Grouping & Routing)

**Goal**: Generalize the second half of the pipeline (Passes 2 and 3) to group and route documents based on the config.
**Requirements**: GRP-01, ORG-01
**Success Criteria**:

1. Pass 2 respects user-defined boundary constraints for grouping pages into documents.
2. Pass 3 routes grouped documents into "Destination Folders" exactly as specified in the configuration.
