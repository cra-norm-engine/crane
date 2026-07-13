# CRANE — CRA Norm Engine
# Copyright (C) 2026 Ali Mohammad Hosseini
# SPDX-License-Identifier: AGPL-3.0-or-later
#
# This file is part of CRANE, free software under the GNU Affero General Public
# License v3.0 or later. See <https://www.gnu.org/licenses/>.

"""
Shared document assets for the generated PDFs.

CE_MARK_DATA_URI is the official CE conformity marking (Regulation (EU)
2024/2847) as an inline PNG data URI. It is embedded directly in the DoC and
package-label templates so WeasyPrint needs no external asset and the mark
prints crisp. The source artwork lives in frontend/CE_marking/ce-mark.png; this
is a tightly-cropped, downscaled copy.
"""

from __future__ import annotations

# Official CE marking, 196x140 PNG, base64-encoded.
CE_MARK_DATA_URI = (
    "data:image/png;base64,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"
)
