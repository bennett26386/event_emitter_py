"""Core implementation for a minimal, synchronous event emitter.

Design decisions taken (one interpretation each, deliberately):

- Wildcards are not supported. The event name is matched exactly by hash key.
  This keeps removal semantics unambiguous and avoids surprising precedence.
- on/once/off return a Listener so callers can remove by the same object.
  off also accepts a name+callable pair for convenience and returns a bool.
- Listeners are called in registration order. once-listeners are removed
  *after* their first call returns, so a raised exception skips removal.
- emit returns the number of listeners that were notified. Reentrancy via
  off during dispatch is safe: listeners still pending get a snapshot taken
  before iteration so structural changes do not corrupt the loop. Removing
  a not-yet-called listener inside a handler prevents that handler from
  firing in the current dispatch (snapshot taken fresh per emit, but off
  mutates the live list).
- Unknown events are a no-op and return zero.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional


Listener = Callable[..., None]


class EventEmitter:
    """A minimal, synchronous, in-process event emitter."""

    def __init__(self) -> None:
        # list per event to preserve registration order; None entries mark
        # once-listeners so they can be differentiated on dispatch.
        self._listeners: Dict[str, List[List[object]]] = {}

    def on(self, name: str, fn: Listener) -> Listener:
        """Register *fn* for *name*. Returns *fn* for chaining/off-by-ref."""
        self._listeners.setdefault(name, []).append([fn, None])
        return fn

    def once(self, name: str, fn: Listener) -> Listener:
        """Register *fn* for *name* to fire a single time; returns *fn*.

        The listener is removed after it returns successfully. If it raises,
        it is left registered so the caller can observe/transiently retry.
        """
        self._listeners.setdefault(name, []).append([fn, True])
        return fn

    def off(self, name: str, fn: Optional[Listener] = None) -> bool:
        """Remove listeners for *name*.

        If *fn* is None, all listeners for *name* are removed.
        Otherwise, the first listener matching *fn* is removed.
        Returns True if anything was removed.
        """
        if name not in self._listeners:
            return False
        slots = self._listeners[name]
        if fn is None:
            if not slots:
                return False
            del self._listeners[name]
            return True
        for i, slot in enumerate(slots):
            if slot[0] is fn or slot[0] == fn:
                del slots[i]
                if not slots:
                    del self._listeners[name]
                return True
        return False

    def listeners(self, name: str) -> List[Listener]:
        """Return a shallow copy of listeners currently registered for *name*."""
        return [slot[0] for slot in self._listeners.get(name, [])]  # type: ignore[list-item]

    def emit(self, name: str, *args: object, **kwargs: object) -> int:
        """Synchronously notify all listeners for *name*.

        Returns the number of listeners notified. Unknown events return 0.
        """
        if name not in self._listeners:
            return 0
        # Snapshot so on/off during dispatch does not corrupt iteration.
        # Live mutations still affect whether a not-yet-called listener fires:
        # off removes from the live list; we filter by identity at call time.
        live = self._listeners[name]
        snapshot = list(live)
        count = 0
        for slot in snapshot:
            fn, once_flag = slot[0], slot[1]  # type: ignore[misc]
            # If removed during this dispatch, skip it.
            if slot not in live:
                continue
            count += 1
            # Call first; only remove if it returned without exception.
            fn(*args, **kwargs)
            if once_flag is True:
                try:
                    live.remove(slot)
                except ValueError:
                    pass
                if not live:
                    del self._listeners[name]
        return count
