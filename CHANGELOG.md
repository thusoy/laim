# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

1.2.0 - 2025-03-18
------------------

### Removed
- Debian packages for buster.

### Added
- Debian packages for bookworm.


1.1.0 - 2022-04-17
------------------

### Changed
- Debian packaging has been refactored to use native debian dependencies instead of dh-virtualenv.
  Handlers that need to install dependencies should install these as regular system packages instead
  of using the venv pip binary to install them.

### Added
- ./tools/build_deb.sh now also builds packages for Debian Bullseye.
- Include both raw and undecoded subject in the message logs.


1.0.1 - 2021-01-02
------------------

### Added
- More log details if the handler fails to process a message.


1.0.0 - 2021-01-01
------------------

### Removed
- Support for python 3.5.

### Changed
- Handlers can now return a dict to add fields to what is logged by the base handler.

### Added
- Added the blinker signal `laim.before_log` to listen to logging events.


0.7.1 - 2020-02-05
------------------

### Fixed
- Actually fix the pip issue that was thought fixed in 0.7.0.


0.7.0 - 2020-01-07
------------------

### Changed
- The license was changed from MIT to the Hippocratic license to deny use that infringes on the UNs
  declaration of human rights.

### Fixed
- The pip in the installed virtualenv was unusable on buster due to a missing dependency in the
  debian package.


0.6.1 - 2019-07-27
------------------

### Fixed
- debian: Don't delete conffiles on remove.


0.6.0 - 2019-07-27
-----------------

### Fixed
- The process title is now set to "laim".


0.5.1 - 2019-07-27
-----------------

### Fixed
- Encoded subjects are now automatically decoded.


0.5.0 - 2019-07-21
------------------

### Added
- You can now customize some SMTP-related parameters through the `smtp_kwargs` constructor
  argument. See the readme for available keys.

### Fixed
- A race condition on startup that could lead to SMTP being handled before dropping privileges.


0.4.0 - 2019-07-20
------------------

### Added
- `unfold` helper to unfold header values.

### Fixed
- Messages with a folded quoted-printable subject wasn't parsed correctly.
- Long subjects are no longer folded in the log output.


0.3.0 - 2019-07-16
------------------

### Fixed
- sendmail: Allow messages without a To header as long as recipients are given on the command line.

### Changed
- Set the syslog facility to mail and identifier to laim.


0.2.0 - 2019-07-10
------------------

### Changed
- Rename the default config file from /etc/laim/conf.yml to /etc/laim/config.yml.


0.1.0 - 2019-07-09
------------------

First release!
