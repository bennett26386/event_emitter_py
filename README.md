# event_emitter_py

A tiny typed event emitter with `once` and `off` semantics. Zero third-party dependencies; standard library only.

## Usage

```python
from event_emitter_py import EventEmitter

ee = EventEmitter()

ee.on("tick", lambda x: print("tick", x))
ee.once("done", lambda: print("finished"))

ee.emit("tick", 1)   # prints: tick 1
ee.emit("done")       # prints: finished
ee.emit("done")       # no-op; the once-listener is gone
```

Exports:

- `EventEmitter` — the emitter class.
- `Listener` — a `Callable[..., None]` type alias for handlers.

Methods:

- `on(name, fn) -> fn` — register a listener; returns `fn` for `off`-by-reference.
- `once(name, fn) -> fn` — register a listener removed after its first successful call.
- `off(name, fn=None) -> bool` — remove one listener by callable, or all for `name` when `fn` is `None`.
- `listeners(name) -> list` — a shallow copy of currently-registered listeners.
- `emit(name, *args, **kwargs) -> int` — notify listeners in registration order; returns the count notified.

## Why

This exists for code that needs a small, dependency-free pub/sub primitive without pulling in a framework. The trade-off: it is synchronous and in-process only, with no wildcards, no async dispatch, and no priority levels. Listeners are called in registration order and exceptions propagate to the caller of `emit`.

## The awkward edge

A `once` listener that raises is **not** removed. Its removal happens after a successful return, so a raised exception leaves the listener registered and a subsequent `emit` will call it again. If you want guaranteed one-shot semantics, catch inside the handler and re-emit or remove explicitly.

Removing a not-yet-called listener from within another listener for the same event during `emit` prevents that pending listener from firing in the same dispatch — `emit` checks the live listener list at each step.
