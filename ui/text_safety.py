# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Qt tooltips may parse rich text; imported content must remain literal."""
from html import escape


def literal_tooltip(value):
    if not value or not any(character in value for character in '<>&'):
        return value
    return '<qt>'+escape(value).replace('\n', '<br>')+'</qt>'
