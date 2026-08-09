---
title: maimai DX Command Reference
description: JiETNG command reference for maimai B50, score tracking, rating breakdown, plate status, song lookup, export, and Import Token.
---

# JiETNG Command Reference

This page follows the current command registry. Commands are case-insensitive unless noted.

Append `-help` to any command to see its usage. Commands that require arguments also show their usage when sent without arguments.

## Account and System

| Command | Description |
|---------|-------------|
| `bind` | Create a binding link for SEGA binding or import-only mode |
| `rebind` | Update SEGA password, version, and Aime |
| `settings` | Open settings and Import Token management |
| `profile` / `getme` | Show account profile and binding state |
| `unbind` / `unbind confirm` | Delete stored user data |
| `maimai update` / `update` | Sync records from maimai NET |
| `export json` / `export xml` | Export processed score data |
| `donate` | Show support information |
| `status` | Show bot runtime status |
| `help` | Show the command directory |

`bind`, `rebind`, `settings`, `update`, `export`, and `unbind` are self-only.

## B-Series Images

| Command | Description |
|---------|-------------|
| `b50` / `best50` | Best 35 + Best 15 |
| `b40` / `best40` | Older rating structure |
| `b35` / `best35` | Old song Best 35 |
| `b15` / `best15` | New song Best 15 |
| `ab35` / `allb35` | All Best 35 |
| `ab50` / `allb50` | All Best 50 |
| `apb50` / `ap50` | AP/AP+ Best 50 |
| `fdxb50` / `fdx50` | FDX/FDX+ Best 50 |
| `rct50` / `r50` | Recent 50 |
| `idealb50` / `idlb50` | Ideal Best 50 |
| `s50` / `sun50` / `寸50` / `寸止め` | Near-miss 50 for SSS+ / SSS: 100.4000%-100.4999%, 99.9000%-99.9999% |

Filters such as `-lv`, `-ra`, `-scr`, `-dx`, `-star`, `-diff`, `-ver`, `-type`, `-next` / `-nxt`, `-page`, and `-times` can be appended.

## Songs and Records

| Format | Description |
|--------|-------------|
| `[song] record` | Personal record for a song |
| `[song] info` | Song details |
| `artist <keyword> [page]` | Search by artist |
| `designer <keyword> [page]` | Search by chart designer |
| `bpm <BPM or range> [page]` | Search by BPM, e.g. `bpm 180` / `bpm 0-120` / `bpm 120-180` |

## Lists and Targets

| Format | Description |
|--------|-------------|
| `[level/constant] records [page]` | Record list |
| `[level/constant] levels` | Level/constant list |
| `[level][target] prog` | Level target status |

Targets: `s`, `s+`, `ss`, `ss+`, `sss`, `sss+`, `fc`, `fc+`, `ap`, `ap+`, `fdx`, `fdx+`.

Target and plate commands support `-uc`, `-up`, and `-c`.

## Plates, Friends, and Tools

| Command | Description |
|---------|-------------|
| `[plate] plate` | Plate status |
| `[version] ver` | Version song list |
| `friend list` / `friends` | maimai friend list |
| `friend-rcd <code> [command] [filters]` | Friend score image |
| `rc <constant>` | Rating table |
| `calc <tap> <hold> <slide> [touch] <break>` | Note score calculator |
| `random [level/constant]` | Random song |
| `rank` / `ranking` / `rank jp` / `rank intl` | Rankings |
| LINE location message | Nearby maimai arcades, merged from JP and INTL sources |
