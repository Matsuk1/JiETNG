# Quick Start

## Prerequisites

- LINE account
- SEGA ID account (for maimai NET)
- Access to maimai NET

## Step 1: Add the Bot

Search for **@299bylay** on LINE or use the link: [@299bylay](https://line.me/R/ti/p/@299bylay)

## Step 2: Bind Your SEGA ID

Send in private chat:

```
bind
```

Click the button the bot sends to open the binding page. Fill in your SEGA ID, password, server version (`jp` or `intl`), and language, then submit to complete binding.

:::warning
Binding tokens expire after 2 minutes. Send `bind` again to get a new link.
:::

## Step 3: Sync Scores

```
maimai update
```

## Step 4: Generate Best 50

```
b50
```

See [Commands Reference](/en/commands/) for all available commands.

---

## Account Management

### Check Binding Status

```
profile
getme
```

### Rebind Account

Update your password, version, and Aime without unbinding (SEGA ID cannot be changed):

```
rebind
```

### Personal Settings

Update timezone, language, background, and other personal settings:

```
settings
```

### Unbind

```
unbind
```

:::warning Data Deletion
Unbinding will **permanently delete** all stored data, including score records, friend lists, and account information. This action cannot be undone.
:::

### Version Selection

Choose the version that matches where you play:

- **jp** (Japan): Playing at arcades in Japan
- **intl** (International): Playing outside Japan

You can change the version later via the `rebind` command without unbinding.

---

## About JiETNG

JiETNG is a 『maimai でらっくす』 score management bot for LINE. It fetches your play data directly from the official SEGA website and generates score charts, supporting Best 50, level analysis, plate progress tracking, and more. Both Japanese (jp) and International (intl) servers are supported.
