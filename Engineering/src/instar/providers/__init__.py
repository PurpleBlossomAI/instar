# SPDX-License-Identifier: Apache-2.0
"""Providers: the seam between the harness and a real model endpoint.

Vendor SDKs are imported lazily inside their own modules, so the mock path stays
stdlib-only and dependency-free.
"""
