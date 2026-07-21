# SPDX-License-Identifier: Apache-2.0
"""Smoke tests: the package installs and imports."""


def test_import_instar() -> None:
    import instar

    assert instar.__doc__ is not None
