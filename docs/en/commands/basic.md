# Basic Commands

## Account Management

### Bind

```
bind
```

Sends a binding link (valid for 2 minutes). Private chat only.

### Unbind

```
unbind
```

Requires confirmation:

```
unbind confirm
```

:::danger Warning
This action is irreversible. All data will be permanently deleted.
:::

### Update Account Settings

```
settings
rebind
```

Sends a settings link to update password, version, timezone, language, Aime, etc. SEGA ID cannot be changed. Private chat only.

### Update Scores

```
maimai update
update
```

Rate limit: maximum 2 requests per 30 seconds.

### View Binding Info

```
profile
getme
```

---

## Calculator

### Achievement Rate Calculator

```
calc <tap> <hold> <slide> [<touch>] <break>
```

4 parameters (no touch) or 5 parameters (with touch):

```
calc 500 100 200 50        # no touch
calc 500 100 200 30 50     # with touch
```

### Rating Table

```
rc 14.7
RC 14.7
Rc 14.7
```

Enter a constant (1.0~15.0, one decimal place max) to view the Rating value for each achievement rate.

---

## Leaderboard

```
rank
ranking
rank jp       # JP server leaderboard
rank intl     # International server leaderboard
```

---

## Random Song

```
random
random 14        # Random Lv.14 song (14.0~14.5)
random 14+       # Random Lv.14+ song (14.6~14.9)
random 14.7      # Random constant 14.7 song
```
