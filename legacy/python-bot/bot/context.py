"""Compatibility seam for incremental extraction from the application facade.

Configuration and legacy helper names are resolved at call time, preserving
operator overrides and existing patch-based tests without circular imports.
Only the composition root binds this context; feature modules do not import
the entry point. New services should accept explicit dependencies instead.
"""


class ApplicationContext:
    def bind(self, namespace):
        self._namespace = namespace

    def __getattr__(self, name):
        try:
            return self._namespace[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


context = ApplicationContext()
