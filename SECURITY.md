<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Security policy

## Reporting a vulnerability

Please report security issues **privately** via GitHub's private vulnerability
reporting for this repository:

> Security → **Report a vulnerability**
> (https://github.com/flxk1/loomground-console/security/advisories/new)

Do not open a public issue for a suspected vulnerability. The maintainer (`@flxk1`)
will acknowledge and coordinate a fix and disclosure.

## Scope notes

- loomground-console is a **client**: it drives RVND's governance surface over MCP
  and holds no governance engine. Governance-engine issues belong to
  [RVND](https://github.com/flxk1/RVND).
- Provider API keys are stored **locally**, encrypted at rest with Fernet under a
  `0600` key file in `~/.config/loomground-console/`. This protects against casual
  reading and accidental commits, **not** against an attacker who already has your
  filesystem (the key sits beside the ciphertext). An OS-keychain backend is on the
  roadmap; treat the local store accordingly.
