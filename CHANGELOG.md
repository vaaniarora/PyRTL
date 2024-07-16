# Changelog

All notable changes to this project will be documented in this file. Only
releases published to PyPI are tracked here. No release candidates!

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added an `initialize_registers` option to `output_to_verilog`
  ([documentation](https://pyrtl.readthedocs.io/en/latest/export.html#pyrtl.importexport.output_to_verilog))

### Changed

- Improved handling of signed integers.

### Fixed

- Fixed a `wire_matrix` bug involving single-element matrices of `Inputs` or `Registers`.

## [0.11.1] - 2024-04-22

### Added

- Named `WireVector` slices with `wire_struct` and `wire_matrix`. See documentation:
  - [wire_struct](https://pyrtl.readthedocs.io/en/latest/helpers.html#pyrtl.helperfuncs.wire_struct)
  - [wire_matrix](https://pyrtl.readthedocs.io/en/latest/helpers.html#pyrtl.helperfuncs.wire_matrix)

### Changed

- Major changes to `render_trace` visualization. See [examples and
  documentation](https://pyrtl.readthedocs.io/en/latest/simtest.html#wave-renderer)
- Many documentation and release process improvements.

### Fixed

- Python 3.11 compatibility.

### Removed

- Python 2.7 support.
