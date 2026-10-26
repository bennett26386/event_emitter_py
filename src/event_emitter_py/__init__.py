"""event_emitter_py: a tiny typed event emitter with once and off semantics."""

from .core import EventEmitter, Listener

__all__ = ["EventEmitter", "Listener"]
