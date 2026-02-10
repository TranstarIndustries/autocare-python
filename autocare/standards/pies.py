"""PIES (Product Information Exchange Standard) version constants.

Defines segment codes, element names, and changes between
PIES 7.2 and PIES 8.0.

PIES 8.0 is backward compatible with 7.2 — all existing Ref# codes
are unchanged. New segments and types are additive.
"""

# Supported versions
VERSIONS = ["7.2", "8.0"]

# --- Segment reference codes (shared across 7.2 and 8.0) ---

SEGMENTS = {
    "A01": "Header",
    "A50": "PriceSheetHeader",
    "A80": "MarketCopy",
    "M01": "DigitalAssetSubSegment",
    "B01": "Item",
    "C01": "Description",
    "D01": "Pricing",
    "E01": "ExtendedProductInfo",
    "F01": "ProductAttribute",
    "H01": "Packaging",
    "J01": "HazardousMaterial",
    "K01": "Kits",
    "N01": "Interchange",
    "P01": "DigitalAssetFileInfo",
    "Z01": "Trailer",
}

# --- PIES 8.0 additions ---

V8_NEW_SEGMENTS = {
    "I01": "PackagingItemsPackage",
}

# All segments in PIES 8.0
SEGMENTS_V8 = {**SEGMENTS, **V8_NEW_SEGMENTS}

# New simple types added in PIES 8.0
V8_NEW_TYPES = [
    "WeightType",
    "LanguageCodeType",
]

# PIES 8.0 is backward compatible — no removed segments or renames
V8_REMOVED_SEGMENTS: dict = {}
V8_RENAMED_SEGMENTS: dict = {}
