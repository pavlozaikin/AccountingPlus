"""Project package initialization."""

# NOTE:
# Third-party dependencies such as ``experta`` rely on the deprecated
# ``collections.Mapping`` attribute that was removed from Python 3.11.
# Importing them without a compatibility shim raises
# ``AttributeError: module 'collections' has no attribute 'Mapping'`` when
# Django executes management commands.  To keep those dependencies working we
# provide the minimal alias to the modern ``collections.abc.Mapping``.
#
# The assignment is safe and mirrors the behaviour of Python versions where
# ``collections.Mapping`` was still exported.  It is evaluated as soon as the
# ``accountingplus`` package is imported (before Django loads installed apps),
# which covers manage.py, ASGI/WSGI entrypoints and tests.
from collections import abc
import collections

if not hasattr(collections, "Mapping"):
    collections.Mapping = abc.Mapping  # type: ignore[attr-defined]
