# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/).


0.5.0 - 2019-07-21
------------------

## Added
- You can now customize some SMTP-related parameters through the `smtp_kwargs` constructor
  argument. See the readme for available keys.

## Fixed
- A race condition on startup that could lead to SMTP being handled before dropping privileges.


0.4.0 - 2019-07-20
------------------

## Added
- `unfold` helper to unfold header values.

## Fixed
- Messages with a folded quoted-printable subject wasn't parsed correctly.
- Long subjects are no longer folded in the log output.


0.3.0 - 2019-07-16
------------------

## Fixed
- sendmail: Allow messages without a To header as long as recipients are given on the command line.

## Changed
- Set the syslog facility to mail and identifier to laim.


0.2.0 - 2019-07-10
------------------

## Changed
- Rename the default config file from /etc/laim/conf.yml to /etc/laim/config.yml.


0.1.0 - 2019-07-09
------------------

First release!
