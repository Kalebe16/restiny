# Change Log

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/)
and this project adheres to [Semantic Versioning](http://semver.org/).

## [0.11.0] - 2025-12-23

### Added

- Pretty-print JSON response body.
- Improve collections tree readability.

## [0.10.0] - 2025-12-09

### Added

- Show last response when reopening a previously executed request.

## [0.9.0] - 2025-12-02

### Added

- OpenAPI spec import.
- File chooser filters by suffix.

## [0.8.0] - 2025-11-20

### Added

- Postman environment import.
- Recursive environment variable references resolution.

### Fixed

- Disable beep sounds.
- Executable build causing DB init failure on startup.

## [0.7.1] - 2025-11-17

### Fixed

- Postman collection import screen title.
- Include SQL files in python package to fix DB initialization.

## [0.7.0] - 2025-11-16

### Added

- Postman collection import.

### Changed

- Editing message headers, parameters, or body no longer activates them automatically; activation is now entirely manual.

## [0.6.3] - 2025-11-11

### Fixed

- Compatibility with Python 3.11, 3.12, and 3.13.

## [0.6.2] - 2025-11-10

### Fixed

- Folder update/delete behavior.

## [0.6.1] - 2025-11-10

### Fixed

- Collections related behaviors.

## [0.6.0] - 2025-11-09

### Added

- Environments.
- Commands pallete.
- **Copy as cURL** command.
- **Manage settings** command.
- **Manage environments** command.
- **Save screenshot** command.
- **Show help panel** command.

### Removed

- **Copy as cURL** shortcut.
- **Open settings** shortcut.

## [0.5.0] - 2025-11-05

### Added

- **Settings** screen with theme selector.
- **Open settings** shortcut.
- HTTP method display in **Collections** area.

## [0.4.2] - 2025-11-04

### Fixed

- Maximize/minimize behavior in **Collections** area.

## [0.4.1] - 2025-11-04

### Fixed

- Python compatibility metadata, removing python 3.10.
- Python 3.11–3.13 compatibility with postponed type annotations.
- Crash when maximizing without focused area.

## [0.4.0] - 2025-11-02

### Added

- `Ctrl+A` shortcut to select all text in input fields.
- Collections support.

## [0.3.0] - 2025-10-19

### Added

- Authentication support (Basic, Bearer, API Key, Digest).

### Fixed

- Issue where whitespace was allowed in the **options-timeout** input field.

## [0.2.1] - 2025-10-18

### Fixed

- Unwanted auto-select behavior when refocusing inputs.
- Focus navigation logic in DynamicFields when removing fields.

## [0.2.0] - 2025-10-15

### Added

- Python 3.14 support.
- Pipeline to publish Python package.
- Pipeline to build executables for arm64 architecture.
- Multipart/form-data body support.

### Fixed

- README image rendering for PyPI compatibility.

## [0.1.2] - 2025-10-11

### Fixed

- Python version metadata — 3.8 and 3.9 were never supported.

## [0.1.1] - 2025-10-09

### Added

- Support for headers, query parameters, and body.
- Support for different body types (RAW, FILE, FORM URLENCODED).
- Options to configure timeout, SSL verification, and follow redirects.
- Automatic `Content-Type` detection in the response to apply syntax highlighting.
- "Copy as cURL" functionality.
- Functionality to maximize specific UI areas.
