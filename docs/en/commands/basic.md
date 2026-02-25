# Basic Commands

This page covers all the essential commands you'll use frequently when working with JiETNG.

## Account Management

### Bind SEGA Account

Link your SEGA ID to start using JiETNG:

```
bind
```

This will provide a web link for secure binding. Private chat only.

### Unbind Account

Remove your SEGA ID and delete all stored data:

```
unbind
```

The bot will ask for confirmation. Send the following to confirm:

```
unbind confirm
```

:::danger Warning
This action is irreversible. All your data will be permanently deleted.
:::

### Update Account Settings

Update your password, timezone, language or Aime settings without unbinding:

```
settings
rebind
```

Sends a link to a web form where you can modify your current account settings. The SEGA ID cannot be changed. Private chat only.

### Update Scores

Fetch your latest scores from SEGA:

```
maimai update
```

## Calculator

### Achievement Rate Calculator

Calculate the percentage needed to reach target achievement rates:

```
calc <tap> <hold> <slide> [<touch>] <break>
```

Example (for a song with 100 taps, 50 holds, 30 slides, 20 touches, 10 breaks):
```
calc 100 50 30 20 10
```

Displays achievement rate values for each note type.

## User Profile

### Get User Information

```
profile
```

## Leaderboard

### DX Rating Leaderboard

View DX Rating rankings among users in your current version:

```
rank
ranking
ランキング
```

You can also specify a version:

```
rank jp
rank intl
```

