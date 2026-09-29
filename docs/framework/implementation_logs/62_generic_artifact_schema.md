# Implementation 62: Generic declared artifact schemas

- Git commit: `237c232`
- Goal: let task packages declare basic output structure without embedding a case-specific scientific schema in the framework.
- Change: output artifacts may declare a schema object. The framework currently validates `json-object@1` and `csv-columns@1`; unsupported or malformed declarations fail before scoring. Schema metadata is included in the artifact inventory.
- Boundary: scientific meanings such as phase-pick semantics remain in task-specific scorers and are not inferred by artifact validation.
- Check: 20 focused artifact, contract and task-validation tests passed; diff validation passed.
