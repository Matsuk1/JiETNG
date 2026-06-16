# Privacy Policy

## Overview

JiETNG is a personally maintained maimai DX score management tool. This page describes the data the current project may collect and process.

## Data Sources

- **SEGA account sync**: the binding page collects SEGA ID, password, server version, and Aime so JiETNG can log in to maimai NET and sync records.
- **Import Token import**: the settings page creates user Import Tokens. The bookmarklet or trusted tools upload processed `profile`, `best`, and `recent` data.

## Stored Data

JiETNG may store LINE user ID, language/timezone/background settings, encrypted SEGA credentials, server version, Aime, maimai profile display data, Best/Recent records, Import Token hashes and status, developer tokens, permission relationships, command usage events, and error logs.

Import Token plaintext is shown once. The server stores a hash.

## Usage

Data is used to sync or import records, generate score images and progress views, provide settings/export/API features, prevent abuse, debug issues, and maintain service stability.

## Third Parties

JiETNG interacts with LINE Platform and SEGA maimai NET. The bookmarklet runs on the official maimai mobile page, but uploaded data is processed score data and does not include the SEGA password.

## Delete and Export

```text
unbind
unbind confirm
```

deletes stored JiETNG user data.

```text
export json
export xml
```

exports processed score data, not internal raw database structures.

## Security

- Web pages use HTTPS.
- SEGA passwords are encrypted at rest.
- Import Tokens and developer tokens should be treated like passwords.
- Revoked tokens cannot keep uploading or accessing resources.

## Contact

- GitHub Issues: [github.com/Matsuk1/JiETNG/issues](https://github.com/Matsuk1/JiETNG/issues)
- Discord: [Join server](https://discord.gg/NXxFn9T8Xz)

Effective date: 2026-06-16
