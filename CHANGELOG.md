# Changelog

All notable changes to this project will be documented in this file.

<!-- The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## [0.3.0] - 2023-06-26

### Added

- Added `deploy` command to deploy all gateway components in a single command
- Added `--http-methods` flag to `add-route` command to specify http methods

## [0.3.1] - 2023-06-27

### Fixed

- Fixed gateway manager failing after deploying due to token refresh desync

## [0.4.0] - 2023-07-03

### Added

- Added CLI support to easily manage JWT authentification to the routes. Please refer to the [auth documentation](./docs/auth.md) for more information on usage.

### Changed

- Grouped CLI commands thematically. The gateway infastructure management is now split from the gateway configuration via different CLI command group.
