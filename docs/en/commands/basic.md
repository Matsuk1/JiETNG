# Basic Commands

Basic commands cover account management, settings, status, export, and support information. Commands are case-insensitive unless noted.

## Account and Settings

```text
bind
```

Sends a private binding link. The page supports full SEGA binding and import-only mode with an Import Token.

```text
rebind
```

Updates SEGA password, server version, and Aime for fully bound users. It cannot change the SEGA ID.

```text
settings
```

Opens the settings page. It manages language, timezone, background, display settings, and Import Tokens. Full SEGA users and Import Token users can both use it.

```text
profile
getme
```

Shows account profile and binding state.

```text
unbind
unbind confirm
```

Deletes stored user data after confirmation.

## Update

```text
maimai update
update
```

Syncs latest records from maimai NET. Requires a full SEGA binding and is self-only.

Import Token users should upload through the bookmarklet.

## Export

```text
export json
export xml
```

Exports processed JiETNG data, not raw database rows. The export includes profile, version, Best records, Recent records, and normalized fields needed to reproduce score images.

## Other Commands

```text
donate
status
rank
rank jp
rank intl
```

`rank` / `ranking` shows DX Rating rankings, optionally scoped to `jp` or `intl`.

## Scope

`bind`, `rebind`, `settings`, `update`, `export`, and `unbind` are self-only. They never operate on mentioned users.
