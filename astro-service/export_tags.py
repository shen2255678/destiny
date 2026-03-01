#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Export _PSYCH_TAG_ZH from prompt_manager.py to destiny-mvp/lib/tagTranslations.json.

Run from astro-service/:
    python export_tags.py
"""
import json
import os
import sys

# Import from local module
sys.path.insert(0, os.path.dirname(__file__))
from prompt_manager import _PSYCH_TAG_ZH  # noqa: E402

OUT = os.path.join(
    os.path.dirname(__file__),
    "..", "destiny-mvp", "lib", "tagTranslations.json"
)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(_PSYCH_TAG_ZH, f, ensure_ascii=False, indent=2)
    f.write("\n")

print(f"Exported {len(_PSYCH_TAG_ZH)} tags → {os.path.normpath(OUT)}")
