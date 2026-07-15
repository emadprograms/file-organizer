# Phase 17 Discussion Log

- **Topic**: YAML File Structure & Format
- **Options**: List vs Dict
- **Decision**: Simple list of strings (`tenants: [name1, name2]`)

- **Topic**: Path Resolution & Filename
- **Options**: Naming convention and path
- **Decision**: File will be named `tenants.yaml` and located in the "source files" directory.

- **Topic**: Validation Strategy
- **Options**: Raw dictionary parsing vs strict Pydantic schema validation
- **Decision**: Strict Pydantic schema validation.

- **Topic**: Translation Strategy
- **Options**: English vs Arabic in YAML
- **Decision**: Tenant names will be written in English. The application logic is responsible for translating them to Arabic.
