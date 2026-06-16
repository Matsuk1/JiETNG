# Getting Started

JiETNG supports two data sources: automatic sync from a bound SEGA account, or processed record uploads through an Import Token and the bookmarklet.

## Requirements

- A LINE account
- One data source:
  - SEGA ID and maimai NET account for `maimai update`
  - or a JiETNG Import Token for bookmarklet uploads

## Bind

Send this in a private chat:

```text
bind
```

The web page lets you choose:

- **Bind a SEGA account**: enter SEGA ID, password, server version (`jp` or `intl`), language, and Aime.
- **Use Import Token without SEGA binding**: create an account that only receives imported records.

Binding links expire. Send `bind` again to get a new link.

## Sync or Import Records

### SEGA Account

```text
maimai update
update
```

The bot syncs profile, Best records, Recent records, and related data from the selected maimai NET version. This command is self-only.

### Import Token

```text
settings
```

Create an Import Token in the settings page, then install the [bookmarklet](/en/bookmarklet). Open the official maimai mobile site, click the bookmarklet, generate an image, and upload best / recent / profile data when needed.

Import Token plaintext is shown only once. The settings page can list tokens, revoke active tokens, and delete revoked tokens.

## Common Commands

```text
b50
rct50
13.6 records
13sss+ progress
真極 achievement
ヒバナ record
settings
export json
```

See [command reference](/en/commands/) and [record commands](/en/commands/record).

## Settings and Rebind

```text
settings
```

Change language, timezone, background, display settings, and Import Tokens.

```text
rebind
```

Update SEGA password, version, and Aime. This is only available to users with a full SEGA binding. The SEGA ID itself cannot be changed through rebind.

## Unbind

```text
unbind
unbind confirm
```

This deletes stored JiETNG user data and cannot be undone.

## JP and INTL

- JP: `https://maimaidx.jp/maimai-mobile/home/`
- INTL: `https://maimaidx-eng.com/maimai-mobile/home/`
