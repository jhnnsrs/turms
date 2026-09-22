# CHANGELOG


## v2.1.2 (2026-09-22)

### Bug Fixes

- **funcs**: Type argument buffers as object and stop them being shadowed
  ([`654be27`](https://github.com/jhnnsrs/turms/commit/654be277cab8a3a14437f75259e1fa90ff55e213))

The generated argument-assembly dicts were `Dict[str, Any]`, which bought no checking and disabled
  what there was. They are write-only buffers whose values come from the enclosing function's
  already-typed parameters, so `Dict[str, builtins.object]` is both accurate and still assignable to
  a `Mapping[str, Any]` parameter.

`builtins.object` rather than a bare `object`, because a schema may name a field `object` -- kraph's
  `assertStructure` does -- which makes it a parameter of the generated function and captures the
  annotation. Qualifying it is the only spelling no field name can take.

For the same reason the input-funcs local is `_data` now: an input type with a `data` field shadowed
  it.

`object` is not assignable to a typed field, so `Cls(**data)` would no longer check; input funcs
  call `Cls.model_validate(_data)` instead, which takes the mapping whole, resolves the same aliases
  and leaves `exclude_unset` reporting exactly the keys that were set -- the @oneOf branch already
  worked this way.

`dict_str_any_annotation` stays as an alias, since turms is published and third-party plugins import
  it.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

Claude-Session: https://claude.ai/code/session_01QEr4a9XNWRms96tmxUPXmz


## v2.1.1 (2026-09-21)

### Bug Fixes

- **ci**: Publish only when semantic-release actually cut a release
  ([`5454b2f`](https://github.com/jhnnsrs/turms/commit/5454b2f61492ee874b4e8051619116d0b6e5a6e8))

`uv publish` ran unconditionally. `semantic-release version` builds only when it cuts a release, so
  any push carrying nothing releasable -- a `build:`, `chore:` or `docs:` change -- left `dist/`
  empty and failed the job on the publish step. Both publish steps are now guarded on
  `hashFiles('dist/**')`, which is the same shape as the guard the tag-only repos get from the
  semantic-release action's `released` output.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

Claude-Session: https://claude.ai/code/session_01QEr4a9XNWRms96tmxUPXmz


## v2.1.0 (2026-09-21)

### Documentation

- **examples**: Repair the rath-usage example
  ([`65513cc`](https://github.com/jhnnsrs/turms/commit/65513cc445d15694e24936ba8bf9da11dde81bcd))

`your_library/proxies.py` imported `current_rath` from `rath.rath` and used it as the fallback in
  all four proxies. That contextvar is gone, so the module raised on import and took `main.py` with
  it.

There is no implicit client to fall back to any more, so the proxies take their rath outright and
  `main.py` passes the one it opened. The generated `your_library/schema.py` is hand-edited to match
  rather than regenerated -- its schema is `countries.trevorblades.com`, so regenerating needs the
  network -- and the same two-line change appears in `README.md` here and in the root `README.md`,
  which repeated "defaults to the currently active client" as if it still meant something.

Also fixes a 9-space list item in the README's config block, which made the YAML it tells you to
  copy invalid.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

### Features

- Client-class generation
  ([`59d8a4a`](https://github.com/jhnnsrs/turms/commit/59d8a4ae510a943ce3e3430f79a90a1432a09cb6))

Baseline commit of the in-flight `client-class` work: `FuncsPlugin` can generate one client class
  per SDK, with `client_class`, `client_bases`, `bound_kwargs`, `reserved_names` and
  `reserved_from`.

Tests: 268 pass, 2 skipped.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

- External_modules, so one project can generate over another's types
  ([`1235f47`](https://github.com/jhnnsrs/turms/commit/1235f477a3f39b76dc5d765ebf20f8428fcda716))

Lets a package ship its wire vocabulary in one module and its fragments, operations and client in a
  second that *imports* the first, instead of regenerating every enum and input into both.

external_modules: - module: rekuest.protocol.schema kinds: [enum, input] from_project:
  rekuest_protocol # optional

Class names are **derived**, not listed: `style_enum_class` and `style_inputtype_class` are pure
  functions of the GraphQL typename and the styler list, so a project declaring the same `stylers:`
  computes exactly the names the other one exported. Nothing reads the other project's output, so
  there is no ordering dependency and no artifact to go stale. `from_project` checks the two styler
  lists agree, which is the only way they can disagree; `names:` is the override when they must.

`ClassRegistry.seed_external` runs before the plugin loop, which is correctness rather than
  tidiness. Left to reference time, a missing input or enum fails quietly: `recurse_type_annotation`
  raises an opaque "did you register this scalar?", a fragment's enum field becomes a string
  annotation whose `model_rebuild()` then fails at import, and `funcs` forward-references its
  literal placeholder into a module-level `SHOULD_NOT_BE_USED.model_rebuild()`.

Imports are registered where a type is *referenced*, not where it is seeded, so an unreferenced
  external type costs nothing.

Two fixes it needed on the way:

- `reference_enum` returned the freshly styled name where `reference_inputtype` returns the map's.
  Identical until a `names:` override exists, wrong the moment one does. -
  `generate_enum`/`generate_inputtype` opened with a bare `assert`, which `run.py` wrapped into an
  unhelpful "EnumsPlugin failed!". They raise a `RegistryError` naming the type now, and the plugins
  skip external types outright rather than colliding.

turms: 277 pass, 2 skipped (268 + 9).

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>


## v2.0.2 (2026-09-01)

### Bug Fixes

- Input funcs respects is union_targert
  ([`c9b05cd`](https://github.com/jhnnsrs/turms/commit/c9b05cd670cd2ab4a8bbf6361510dd073d4845a1))


## v2.0.1 (2026-08-24)

### Bug Fixes

- **strawberry**: Give omittable input fields a Python default
  ([`f389cf9`](https://github.com/jhnnsrs/turms/commit/f389cf9416eeb66f47d5066b2a287d15bc948751))

StrawberryPlugin.generate_inputs() only ever passed description/ deprecation_reason to
  strawberry.field(...), never reading a field's GraphQL default_value. An input field a caller is
  allowed to omit - because it's nullable, or because the schema gives it a default - was still
  generated as a required keyword-only argument on the dataclass. Any client omitting the field
  crashed construction with a "missing required keyword-only argument" TypeError instead of falling
  back to null/the schema default.

InputsPlugin (used for client-side codegen) already computes this correctly via
  has_default/omittable; this mirrors that logic for the server-side StrawberryPlugin, reusing the
  existing default/default_factory convention from default_generate_directives for mutable
  (list/dict) defaults.


## v2.0.0 (2026-08-24)

### Bug Fixes

- Description
  ([`2b8a5d3`](https://github.com/jhnnsrs/turms/commit/2b8a5d394a3c5049f7e7380237f58595da0eca86))

- Newer python support
  ([`697c8a5`](https://github.com/jhnnsrs/turms/commit/697c8a5214b9f33d1a06ceb7c7133779b60f4879))

- Removal of faulty examples
  ([`6349936`](https://github.com/jhnnsrs/turms/commit/6349936179a8d7144f0a1623c81a95da06629635))

### Features

- Input types have now validation aliases and serialization aliases
  ([`ed1c155`](https://github.com/jhnnsrs/turms/commit/ed1c155adb122d9d5b9fbcabc2a9e7047c7330d5))

- More spec compliance (skip include etc)
  ([`b69090e`](https://github.com/jhnnsrs/turms/commit/b69090e658171a113c0bbbd35d390c5489bf3aaf))

- New annotation modes
  ([`bbd2ca7`](https://github.com/jhnnsrs/turms/commit/bbd2ca74c7de39232f2578aee31fb3f1b9c27c23))

- Rewritten for pydantic v2
  ([`fbd6eca`](https://github.com/jhnnsrs/turms/commit/fbd6ecaf494bd5f62996b6431e70a5d97b1d18d9))

### Refactoring

- Drop the pydantic v1 option spellings
  ([`a8b5b17`](https://github.com/jhnnsrs/turms/commit/a8b5b17e4ca241d78d5b241437c430c995ac1a14))

`OptionsConfig` could still emit `allow_mutation` and `orm_mode` into the generated `model_config`.
  Both are pydantic v1 keys that v2 rejects, so every consuming project importing such a module got
  a `UserWarning` ("'allow_mutation' has been removed" / "'orm_mode' has been renamed to
  'from_attributes'") and the option silently did nothing.

- `orm_mode` is replaced by `from_attributes`, which is what actually reaches the generated
  `ConfigDict`. - `allow_mutation` has no v2 equivalent here; immutable models are the `freeze`
  section's job, so the key is gone rather than silently translated.

Both spellings are intercepted by a before-validator that names the replacement — `OptionsConfig`
  forbids extras, so otherwise they would have failed as an anonymous "extra inputs are not
  permitted".

`unit_test_with` gains `strict_warnings`, which runs the generated module under `-W
  error::UserWarning`. The generated code executes in a subprocess, so a filter set by the test
  process never reached it; without this the new regression test passes even with a v1 key
  re-introduced.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

- Normalize the deprecated pydantic_version key away
  ([`336cf7f`](https://github.com/jhnnsrs/turms/commit/336cf7f5c9389ff90e783da2b2c1524866c5a7ee))

Storing the accepted "v2" value meant a dumped configuration carried the dead key forward into
  generated project.json files. The validator now returns None once the v1 check has passed.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>

- Remove the pydantic v1 generation target
  ([`388e3ee`](https://github.com/jhnnsrs/turms/commit/388e3eec60e3e4ee09ffadec2497699f5cbefbe2))

Turms now only emits pydantic v2 code. The forked generation paths are gone and the v2 arm is
  unconditional:

- `generate_config_class_pydantic` (the v1 `class Config:` emitter) and the
  `generate_pydantic_config` dispatcher are deleted; the former `generate_config_dict` takes over
  the `generate_pydantic_config` name. - forward references always resolve via `model_rebuild()`
  (was `update_forward_refs()` on v1). - discriminated unions and direct `@oneOf` unions are no
  longer gated behind a version check, so they lose their degraded wrapper-class fallback.

`pydantic_version` stays accepted as a no-op so existing configurations that say `pydantic_version:
  v2` keep loading; `v1` now raises a validation error naming the release and the migration.

Also fixes the surviving v2 arm of `generate_arguments_config`, which gated on
  `plugin_config.arguments_allow_population_by_field_name is not None` (a bool, so always true) and
  then read the unrelated `config.options.allow_population_by_field_name`. Every generated
  `Arguments` class carried a junk `model_config = ConfigDict(populate_by_name=None)` and the plugin
  flag did nothing. It now emits `populate_by_name=True` only when the flag is set, and nothing
  otherwise.

The four `*_v1.py` test modules are removed; the tests parametrized over `["v1", "v2"]` keep their
  v2 case. `test_multiple_forward_references` asserted on the v1 `update_forward_refs` spelling and
  so matched nothing under the v2 default — it now asserts on `model_rebuild` and that the calls are
  actually present.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>


## v1.2.1 (2026-08-02)

### Bug Fixes

- No two kinds of literals
  ([`c9f2b8b`](https://github.com/jhnnsrs/turms/commit/c9f2b8b1713d94bc5c59d2cfe217c26bea4f58fc))


## v1.2.0 (2026-07-31)

### Features

- Oneof support + unionElementof (discriminated union)
  ([`38a39ef`](https://github.com/jhnnsrs/turms/commit/38a39ef9b4d8f498fea34216327af426193583c0))


## v1.1.0 (2026-07-27)

### Features

- Add coercible inputs (beyond scalars)
  ([`2fd2279`](https://github.com/jhnnsrs/turms/commit/2fd2279b0e25c91865af23e84cb86f6fc0f6d086))


## v1.0.1 (2026-07-06)

### Bug Fixes

- Add interface to type coercion on specific narrow type mutations
  ([`e044a8c`](https://github.com/jhnnsrs/turms/commit/e044a8cb88da3765dc257403b6327464de7431b9))


## v1.0.0 (2026-06-22)

### Bug Fixes

- Input funcs
  ([`bc3aa14`](https://github.com/jhnnsrs/turms/commit/bc3aa14541e530ad4f2cfc1483a5f929a5792b93))

### Features

- Document UNSET defaults model and input_funcs plugin
  ([`caad384`](https://github.com/jhnnsrs/turms/commit/caad38464eb833f060733b33f107a06502f48ad9))

GraphQL schema defaults are no longer baked into the generated client: defaulted fields become
  optional `= None` and the value is owned by the server. Convenience functions default optionals to
  an UNSET sentinel and build the payload conditionally, so callers must serialize with
  exclude_unset=True — a breaking change for existing executor proxies.

- add migration guide (migration-defaults-unset) covering the UNSET model, the
  GraphQLDefault/Deprecated markers, and the required proxy change - add reference page for the new
  input_funcs factory plugin - document the new global config options (coercible_scalars,
  graphql_default_class, deprecated_class, document_field_metadata, unset_type_class,
  unset_instance) and the InputFuncsPlugin row - note the exclude_unset contract in the funcs plugin
  docs

BREAKING CHANGE: executor proxies must serialize variables with exclude_unset=True; schema defaults
  are no longer baked into client models.

- Fixes the default type
  ([`2ea0361`](https://github.com/jhnnsrs/turms/commit/2ea03614d9fa128393c0334d1f85e46b071b3bbf))

### Breaking Changes

- Executor proxies must serialize variables with exclude_unset=True; schema defaults are no longer
  baked into client models.


## v0.12.0 (2026-06-12)

### Bug Fixes

- New teadme and autodetect env
  ([`15d52f7`](https://github.com/jhnnsrs/turms/commit/15d52f7aa987c46c5c44e5745acc5ef2b4e4c3db))

### Features

- Add template plus documentation section
  ([`f663e25`](https://github.com/jhnnsrs/turms/commit/f663e25e41d4b3b4903fd427b5e9d326189e50fb))


## v0.11.0 (2026-06-12)


## v0.10.3 (2026-06-12)

### Features

- Add ruff
  ([`d587bd0`](https://github.com/jhnnsrs/turms/commit/d587bd09b18a1debe996cf43c5c12adff84da870))


## v0.10.2 (2026-04-13)

### Bug Fixes

- Add copilot insturctions
  ([`db4c9b0`](https://github.com/jhnnsrs/turms/commit/db4c9b0ac2d6002d7de9c662ac6361a3430c21c9))

- Add strawberry one of support
  ([`b8d5cd8`](https://github.com/jhnnsrs/turms/commit/b8d5cd8fc5668569bbd8a0fe13adb9f1c98d0d94))

- Fi support for spread in union
  ([`84b70a8`](https://github.com/jhnnsrs/turms/commit/84b70a8a9c22cffb976c2143d27d518ac293d462))

- Trying to
  ([`a25d6a9`](https://github.com/jhnnsrs/turms/commit/a25d6a96d0bf63b5ecd5ee67fcf776005387a9f5))


## v0.10.1 (2025-10-29)

### Bug Fixes

- Ensure deterministic output by sorting
  ([`1035bbb`](https://github.com/jhnnsrs/turms/commit/1035bbb785ea45f9978b2464b9b627872efd7743))


## v0.10.0 (2025-08-22)

### Features

- Add abbility to omit graphql validation rules if unessaary
  ([`78dffa7`](https://github.com/jhnnsrs/turms/commit/78dffa780975da4b5c145a8bb2407f5d4d2ee4dd))


## v0.9.2 (2025-07-30)

### Bug Fixes

- Add suport for deterministic output order
  ([`957d152`](https://github.com/jhnnsrs/turms/commit/957d1521bee013c08d1ab6d6863f5eda10bd53bc))

Sort document files to produce deterministict output order.

- Add support for topological ordering
  ([`768ffa3`](https://github.com/jhnnsrs/turms/commit/768ffa39518c2e7056c8319686bd47db4a514ea4))


## v0.9.1 (2025-07-30)

### Bug Fixes

- Add more tests
  ([`fc20d3e`](https://github.com/jhnnsrs/turms/commit/fc20d3eac7fe23433692c0d7c4a63eebab5280f0))


## v0.9.0 (2025-05-15)

### Features

- Added in "coercible types" that allow for the funcs plugin to provide a union typealis for all
  values that are coercible through the pydantic serialization.
  ([`7fb38d4`](https://github.com/jhnnsrs/turms/commit/7fb38d4770af69442f33aa8eb5b775f2ffc9f91d))


## v0.8.7 (2025-05-12)

### Bug Fixes

- Add requests dependency to project and update version in lock file
  ([`7df85d4`](https://github.com/jhnnsrs/turms/commit/7df85d4d40b1f435e6f2040576203b0307cd5261))


## v0.8.6 (2025-05-12)

### Bug Fixes

- Add Python 3.10 to CI workflow matrix and clean up test command
  ([`b828fc3`](https://github.com/jhnnsrs/turms/commit/b828fc39f983e7dc7fae241cb5efa15ff0fcc051))

- Update installation instructions in README
  ([`f7e30ca`](https://github.com/jhnnsrs/turms/commit/f7e30ca7c2b7d9800b8144b740cb07e1db150c37))

- Update semantic release
  ([`442e2d3`](https://github.com/jhnnsrs/turms/commit/442e2d38912e2cef195d390e022ed655ccb3991a))


## v0.8.5 (2025-05-12)

### Bug Fixes

- Add semantic release and pin python version
  ([`1282d81`](https://github.com/jhnnsrs/turms/commit/1282d81a52e1975463f70a1650ea5fca16ba3c4c))

- Changed readme
  ([`ab89ba1`](https://github.com/jhnnsrs/turms/commit/ab89ba17e0fe31600a9c7d19c08810e6c95cd60f))

### Features

- Typing + semantic release
  ([`3faafe3`](https://github.com/jhnnsrs/turms/commit/3faafe31d2d8337f411d9976e673c1f5b04a3b60))


## v0.8.4 (2024-12-15)


## v0.8.3 (2024-11-15)


## v0.7.0 (2024-11-12)


## v0.6.0 (2024-09-20)


## v0.5.0 (2024-01-23)


## v0.4.3 (2023-07-18)


## v0.4.2 (2023-05-01)


## v0.4.0 (2023-03-18)


## v0.3.1 (2023-02-24)


## v0.3.0 (2023-01-13)

### Bug Fixes

- Double fragments, fix: mypy typing
  ([`96c0f8f`](https://github.com/jhnnsrs/turms/commit/96c0f8f2f219a7fb36c3022af3da082713289a71))

- Failing test
  ([`9b44d7a`](https://github.com/jhnnsrs/turms/commit/9b44d7a95171cd13a38b9e7baed9a8047845f59b))

- Funcs: if args are list
  ([`924ab30`](https://github.com/jhnnsrs/turms/commit/924ab303e889b7a403db7334a1b2b128264130d8))

- Missing field, added optional dep isort
  ([`787e594`](https://github.com/jhnnsrs/turms/commit/787e594e4df591b682abc69be184a778823aa094))

- Remove tests
  ([`dcd599a`](https://github.com/jhnnsrs/turms/commit/dcd599a72b87d9d764f4d3b4dfdc56b60aef8312))

- Typo
  ([`0425017`](https://github.com/jhnnsrs/turms/commit/0425017f66a8e22d922fba30c3a48c9bf2d359ed))

### Features

- Documentation support for operations
  ([`00adc6b`](https://github.com/jhnnsrs/turms/commit/00adc6b13fb68d2b479bd5135f1235efc9172f44))
