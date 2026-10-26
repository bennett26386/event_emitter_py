"""Behavioural tests for event_emitter_py.core.EventEmitter."""

import unittest

from event_emitter_py import EventEmitter, Listener  # noqa: F401
from event_emitter_py.core import EventEmitter as CoreEventEmitter


class TestEventEmitter(unittest.TestCase):
    def test_on_and_emit_basic(self):
        ee = EventEmitter()
        seen = []
        ee.on("go", lambda *a: seen.append(a))
        n = ee.emit("go", 1, 2)
        self.assertEqual(n, 1)
        self.assertEqual(seen, [(1, 2)])

    def test_emit_unknown_returns_zero(self):
        ee = EventEmitter()
        self.assertEqual(ee.emit("nope"), 0)

    def test_multiple_listeners_called_in_order(self):
        ee = EventEmitter()
        order = []
        ee.on("e", lambda: order.append("a"))
        ee.on("e", lambda: order.append("b"))
        ee.on("e", lambda: order.append("c"))
        n = ee.emit("e")
        self.assertEqual(n, 3)
        self.assertEqual(order, ["a", "b", "c"])

    def test_once_fires_only_once(self):
        ee = EventEmitter()
        calls = []
        ee.once("e", lambda x: calls.append(x))
        ee.emit("e", 1)
        ee.emit("e", 2)
        self.assertEqual(calls, [1])

    def test_once_removed_after_successful_call(self):
        ee = EventEmitter()
        ee.once("e", lambda: None)
        self.assertEqual(len(ee.listeners("e")), 1)
        ee.emit("e")
        self.assertEqual(ee.listeners("e"), [])

    def test_once_not_removed_when_it_raises(self):
        ee = EventEmitter()

        def bad():
            raise ValueError("boom")

        ee.once("e", bad)
        self.assertEqual(len(ee.listeners("e")), 1)
        with self.assertRaises(ValueError):
            ee.emit("e")
        # Still registered because it raised.
        self.assertEqual(len(ee.listeners("e")), 1)

    def test_mixed_on_and_once(self):
        ee = EventEmitter()
        calls = []
        ee.on("e", lambda: calls.append("on"))
        ee.once("e", lambda: calls.append("once"))
        ee.emit("e")
        ee.emit("e")
        self.assertEqual(calls, ["on", "once", "on"])

    def test_off_by_function(self):
        ee = EventEmitter()
        a = lambda: None
        b = lambda: None
        ee.on("e", a)
        ee.on("e", b)
        self.assertTrue(ee.off("e", a))
        self.assertEqual(ee.listeners("e"), [b])

    def test_off_unknown_function_returns_false(self):
        ee = EventEmitter()
        ee.on("e", lambda: None)
        self.assertFalse(ee.off("e", lambda: None))

    def test_off_all_for_event(self):
        ee = EventEmitter()
        ee.on("e", lambda: None)
        ee.on("e", lambda: None)
        self.assertTrue(ee.off("e"))
        self.assertEqual(ee.listeners("e"), [])

    def test_off_unknown_event_returns_false(self):
        ee = EventEmitter()
        self.assertFalse(ee.off("missing"))
        self.assertFalse(ee.off("missing", lambda: None))

    def test_emit_kwargs(self):
        ee = EventEmitter()
        captured = {}
        ee.on("e", lambda **kw: captured.update(kw))
        ee.emit("e", x=1, y=2)
        self.assertEqual(captured, {"x": 1, "y": 2})

    def test_off_during_dispatch_prevents_pending(self):
        # Removing a not-yet-called listener during dispatch should skip it.
        ee = EventEmitter()
        log = []

        def second():
            log.append("second")

        def first():
            log.append("first")
            ee.off("e", second)

        ee.on("e", first)
        ee.on("e", second)
        n = ee.emit("e")
        self.assertEqual(log, ["first"])
        self.assertEqual(n, 1)
        self.assertEqual(ee.listeners("e"), [first])

    def test_on_returns_same_function(self):
        ee = EventEmitter()
        fn = lambda: None
        self.assertIs(ee.on("e", fn), fn)
        self.assertIs(ee.once("e", fn), fn)

    def test_listeners_returns_copy(self):
        ee = EventEmitter()
        fn = lambda: None
        ee.on("e", fn)
        lst = ee.listeners("e")
        lst.clear()
        self.assertEqual(ee.listeners("e"), [fn])

    def test_exported_names_match_core(self):
        self.assertIs(EventEmitter, CoreEventEmitter)


if __name__ == "__main__":
    unittest.main()
