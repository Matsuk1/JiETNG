# JiETNG Local Plugins

Put local plugin files in this directory to add lightweight bot commands without
editing `main.py`.

Each plugin is a Python file that exposes `register(api)`.

```python
def register(api):
    api.command("ping", ping, name="plugin_ping")


def ping(ctx, api):
    return api.text("pong")
```

Plugins are loaded at startup from `config.json`:

```json
{
  "plugins": {
    "enabled": true,
    "directories": ["./plugins"]
  }
}
```

## Command API

- `api.command(matcher, handler, name=None, before_core=False, mention_queryable=False, self_only=False, rate_limit_key=None)`
- `api.exact("word", handler=handler)`
- `api.prefix("prefix ", handler=handler)`
- `api.regex(r"^pattern$", handler=handler)`
- `api.text("message")`

`handler` receives the normal JiETNG command context:

```python
def handler(ctx, api):
    # ctx.text, ctx.user_id, ctx.source_type, ctx.match, ctx.is_mention, ...
    return api.text("reply")
```

By default plugin commands are checked after core commands. Set
`before_core=True` only when a plugin intentionally overrides a core command.

## Long Sessions

Plugins can start an in-memory session for follow-up messages:

```python
def start(ctx, api):
    api.start_session(ctx, play, state={"count": 0}, ttl=1800, scope="chat")
    return api.text("Session started")


def play(ctx, session, api):
    session.state["count"] += 1
    if ctx.text == "end":
        session.end()
        return api.text("Session ended")
    return api.text(f"Message #{session.state['count']}")
```

Session scopes:

- `chat`: one session for the private chat, group, or room.
- `user`: one session for the user across chats.
- `user_chat`: one session for this user inside this chat.

While a session is active, normal text is delivered to the session before command
matching. Prefix a message with `/` to bypass the active session and run a normal
command, for example `/b50` runs `b50`.
