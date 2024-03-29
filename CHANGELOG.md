# Changelog

All notable changes to this project will be documented in this file.

<!-- The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html). -->

## [0.6.1] - 2023-07-17

### Changed

- Improved pypi.org package description

## [0.6.0] - 2023-07-13

### Added

- A profile can now be specified via the `--profile` flag or the `SCW_PROFILE` environment variable. This allows to use a different profile than the default one configured in the Scaleway CLI.

### Changed

- Improved logging, and added a `--debug` flag to the CLI to enable debug logs during command execution.
- Raised Kong default log-level to `warn` to reduce the amount of logs generated by the gateway.
- Improved documentation
- Improved error handling and better feedback for users when an error occurs.
- Added JWT and Cors information to the `route ls` command.

### Fixed

- Missing client validation leading to errors when using the CLI with an invalid configuration.
- Deletion of the gateway would not clean-up all resources when some were missing.

## [0.5.0] - 2023-07-11

### Added

- Documentation is now available on [readthedocs](https://serverless-gateway.readthedocs.io/en/latest/).
- Added utilties to manage custom domains for your gateway. Please refer to the [custom domain documentation](https://serverless-gateway.readthedocs.io/en/latest/domains.html) for more information on usage.
- Kong statsd dashboard will now be automatically imported to your Cockpit when using the `deploy` command.
- Improved CLI experience by adding some more progress feedback.

## [0.4.0] - 2023-07-03

### Added

- Added CLI support to easily manage JWT authentification to the routes. Please refer to the [auth documentation](https://serverless-gateway.readthedocs.io/en/latest/auth.html) for more information on usage.

### Changed

- Grouped CLI commands thematically. The gateway infastructure management is now split from the gateway configuration via different CLI command group.

## [0.3.1] - 2023-06-27

### Fixed

- Fixed gateway manager failing after deploying due to token refresh desync

## [0.3.0] - 2023-06-26

### Added

- Added `deploy` command to deploy all gateway components in a single command
- Added `--http-methods` flag to `add-route` command to specify http methods
