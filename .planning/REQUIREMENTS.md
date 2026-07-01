# Requirements

## v1 Requirements

### Configuration
- [ ] **CONF-01**: Parse user-provided configuration file (YAML or JSON) to define the routing and instructions.
- [ ] **CONF-02**: Provide a sample configuration file (`sample-config.yaml`) replicating the existing tenant structure.
- [ ] **CONF-03**: Create a private local configuration for regression testing.

### Extraction & Cleaning
- [ ] **EXT-01**: Update Pass 1 to use config-defined metadata extraction instructions.
- [ ] **EXT-02**: Update Pass 1.5 to execute config-defined global cleaning and interpolation rules.

### Grouping & Organization
- [ ] **GRP-01**: Update Pass 2 to group pages based on config-defined boundary rules.
- [ ] **ORG-01**: Update Pass 3 to route documents into user-defined "Destination Folders".

## v2 Requirements

(None)

## Out of Scope

- Changing the underlying Python pipeline architecture (ingestion, 4 passes) — Keep the engine the same, only externalize the rules.

## Traceability

*(Populated during roadmap creation)*
