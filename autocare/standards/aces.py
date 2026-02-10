"""ACES (Aftermarket Catalog Exchange Standard) version constants.

Defines element names, attribute names, and breaking changes between
ACES 4.2 and ACES 5.0.
"""

# Supported versions
VERSIONS = ["4.2", "5.0"]

# --- ACES 4.2 element names ---

V4_ELEMENTS = [
    "ACES",
    "Header",
    "App",
    "Part",
    "PartType",
    "MfrBodyCode",
    "Qty",
    "Position",
    "Qualifier",
    "Note",
    "Comment",
    "References",
    "DiagramReference",
    "AssetReference",
    "MfrLabel",
    "DisplayOrder",
    "AssetName",
]

# --- ACES 5.0 element names ---

V5_ELEMENTS = [
    "ACES",
    "Header",
    "App",
    "PartNumber",
    "PartTerminology",
    "MfrBodyCode",
    "Qty",
    "Position",
    "Qualifier",
    "Note",
    "Comment",
    "DiagramAsset",
    "NonDiagramAssets",
    "NonDiagramAsset",
    "MfrLabel",
    "DisplayOrder",
    "AssetName",
]

# --- Breaking changes: ACES 4.2 -> 5.0 ---

# Element renames: old_name -> new_name
V4_TO_V5_ELEMENT_RENAMES = {
    "Part": "PartNumber",
    "PartType": "PartTerminology",
}

V5_TO_V4_ELEMENT_RENAMES = {v: k for k, v in V4_TO_V5_ELEMENT_RENAMES.items()}

# Elements removed in 5.0
V5_REMOVED_ELEMENTS = [
    "References",
    "DiagramReference",
    "AssetReference",
]

# Elements added in 5.0
V5_NEW_ELEMENTS = [
    "DiagramAsset",
    "NonDiagramAssets",
    "NonDiagramAsset",
]

# Attribute renames in ACES 5.0 (on the App element)
V4_TO_V5_ATTRIBUTE_RENAMES = {
    "BrandAAIAID": "BrandID",
}

V5_TO_V4_ATTRIBUTE_RENAMES = {v: k for k, v in V4_TO_V5_ATTRIBUTE_RENAMES.items()}

# Attributes removed in 5.0
V5_REMOVED_ATTRIBUTES = {
    "param": ["lang"],  # "lang" attribute removed from <param> element
}

# Field-level renames for record migration (used by compatibility layer)
V4_TO_V5_FIELD_RENAMES = {
    "Part": "PartNumber",
    "PartType": "PartTerminology",
    "BrandAAIAID": "BrandID",
}

V5_TO_V4_FIELD_RENAMES = {v: k for k, v in V4_TO_V5_FIELD_RENAMES.items()}
