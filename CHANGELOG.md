# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [unreleased]

### Added

- Added `Ctrl+A` shortcut to select all text in input fields.

## [0.3.0] - 2025-10-19

### Added

- Added authentication support (Basic, Bearer, API Key, Digest).

### Fixed

- Fixed issue where whitespace was allowed in the **options-timeout** input field.

## [0.2.1] - 2025-10-18

### Fixed

- Fixed unwanted auto-select behavior when refocusing inputs.
- Fixed focus navigation logic in DynamicFields when removing fields.

## [0.2.0] - 2025-10-15

### Added

- Added Python 3.14 support.
- Added pipeline to publish Python package.
- Added pipeline to build executables for arm64 architecture.
- Added multipart/form-data body support.

### Fixed

- Fixed README image rendering for PyPI compatibility.

## [0.1.2] - 2025-10-11

### Fixed

- Fixed Python version metadata — 3.8 and 3.9 were never supported.

## [0.1.1] - 2025-10-09

### Added

- Added support for headers, query parameters, and body.
- Added support for different body types (RAW, FILE, FORM URLENCODED).
- Added options to configure timeout, SSL verification, and follow redirects.
- Added automatic `Content-Type` detection in the response to apply syntax highlighting.
- Added "Copy as cURL" functionality.
- Added functionality to maximize specific UI areas.
