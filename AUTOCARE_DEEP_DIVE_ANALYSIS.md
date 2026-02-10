# 🚗 Auto Care Association Deep Dive Analysis

> **Prepared for:** Transtar Industries
> **Date:** February 4, 2026
> **Scope:** Reference Database Analysis, API Migration Planning, Ingestion Architecture

---

## 📋 Table of Contents

1. [Executive Summary](#-executive-summary)
2. [Auto Care Reference Databases Overview](#-auto-care-reference-databases-overview)
3. [API Version Comparison](#-api-version-comparison)
4. [Current Database Schema Analysis](#-current-database-schema-analysis)
5. [Breaking Changes & Deprecations](#-breaking-changes--deprecations)
6. [Architecture Recommendations](#-architecture-recommendations)
7. [AWS Database Migration Options](#-aws-database-migration-options)
8. [Dagster Ingestion Design](#-dagster-ingestion-design)
9. [autocare-python Update Plan](#-autocare-python-update-plan)
10. [Implementation Roadmap](#-implementation-roadmap)

---

## 🎯 Executive Summary

### The Challenge
Transtar Industries maintains automotive part reference data derived from Auto Care Association standards. The association is releasing **major version updates** effective **January 28, 2026**:

| Standard | Current | New | Effective Date |
|----------|---------|-----|----------------|
| ACES | 4.2 | **5.0** | 1/28/2026 |
| PIES | 7.2 | **8.0** | 10/2/2025 ✅ (already live) |
| VCdb | 1.0 | **2.0** | 1/28/2026 |
| PAdb | 4.0 | **5.0** | 1/28/2026 |

### Key Findings

1. **🔴 PIES 8.0 is already live** - Migration should have started October 2025
2. **🟡 11 months until ACES 5.0/VCdb 2.0/PAdb 5.0** - Time to plan carefully
3. **Breaking changes identified** - Element renames, schema restructuring
4. **Current infrastructure is solid** - VCDB schema, hierarchyid approach, PIES attributes well-designed
5. **✅ Incremental loading supported** - All tables have `EffectiveDateTime`/`EndDateTime` fields for delta sync

### Recommended Architecture

```
Auto Care API → Dagster → Aurora PostgreSQL → Fivetran → Snowflake
                          (source of truth)    (CDC)     (analytics)
                                │
                                ▼
                          Application APIs
```

- **Dagster** extracts/transforms, writes to Aurora only (single target)
- **Aurora PostgreSQL** serves as operational database (low-latency queries)
- **Fivetran** replicates to Snowflake via CDC (native PostgreSQL connector)
- **Snowflake** handles analytics, BI, data science workloads

### Recommended Actions

1. **Immediate:** Begin PIES 8.0 migration (Packaging Items segment support)
2. **Q1 2026:** Update autocare-python library for new API versions
3. **Q2-Q3 2026:** Provision Aurora PostgreSQL + deploy Dagster ingestion pipeline
4. **Q4 2026:** Documentation, training, and January 2026 version cutover

---

## 📚 Auto Care Reference Databases Overview

### What is Auto Care Association?

The Auto Care Association is the **national trade association** for the $500B+ U.S. automotive aftermarket industry. They maintain standardized reference databases that enable:

- **Vehicle Identification** - Consistent way to describe any vehicle configuration
- **Part Classification** - Standardized product categories and terminology
- **Fitment Data** - Which parts fit which vehicles
- **Product Information** - Standardized product attributes and specifications

### The Core Databases

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     AUTO CARE REFERENCE DATABASE ECOSYSTEM                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐             │
│   │  VCdb   │     │  PCdb   │     │  PAdb   │     │   Qdb   │             │
│   │ Vehicle │     │  Part   │     │ Product │     │Qualifier│             │
│   │ Config  │     │ Class   │     │  Attr   │     │  Data   │             │
│   └────┬────┘     └────┬────┘     └────┬────┘     └────┬────┘             │
│        │               │               │               │                   │
│        └───────────────┴───────┬───────┴───────────────┘                   │
│                                │                                           │
│                    ┌───────────┴───────────┐                               │
│                    │                       │                               │
│              ┌─────┴─────┐           ┌─────┴─────┐                         │
│              │   ACES    │           │   PIES    │                         │
│              │ (Fitment) │           │ (Product) │                         │
│              └───────────┘           └───────────┘                         │
│                                                                             │
│   ┌─────────────┐                                                          │
│   │ Brand Table │  28,000+ brands with AAIA IDs                           │
│   └─────────────┘                                                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Database Details

#### 🚙 VCdb (Vehicle Configuration Database)
**Purpose:** Define every vehicle configuration sold in North America

| Metric | Value |
|--------|-------|
| Vehicle Applications | 175,500+ |
| System Configurations | 2,400,000+ |
| Update Frequency | Monthly (API: Daily) |

**Key Tables:**
- `BaseVehicle` - Year/Make/Model combinations
- `Vehicle` - BaseVehicle + SubModel
- `Engine` - Engine configurations (liter, cylinders, fuel type, aspiration)
- `Transmission` - Transmission types (speeds, control type, manufacturer)
- `DriveType` - 2WD, 4WD, AWD, etc.
- `BedType`, `BodyType`, `BrakeSystem`, `SpringType`, `SteeringSystem`...

**Hierarchy Structure:**
```
Year → Make → Model → SubModel → [Engine | Transmission | DriveType | ...]
```

#### 🔧 PCdb (Product Classification Database)
**Purpose:** Standardized part terminology and categorization

| Metric | Value |
|--------|-------|
| Part Terminologies | 40,000+ |
| Categories | Hierarchical tree structure |

**Example:**
```
Category: Brake System
  └── Subcategory: Disc Brake
        └── Part Type: Brake Pad Set (ID: 1684)
```

#### 📊 PAdb (Product Attribute Database)
**Purpose:** Define product attributes and their valid values

| Metric | Value |
|--------|-------|
| Attributes | 9,700+ |
| Associations | 141,700+ |

**Example Attributes:**
- Material Type
- Finish
- Dimensions (Length, Width, Height)
- Weight
- Color
- Warranty Period

#### ❓ Qdb (Qualifier Database)
**Purpose:** Conditional fitment qualifiers

| Metric | Value |
|--------|-------|
| Qualifiers | 26,000+ |

**Example Qualifiers:**
- "With Air Conditioning"
- "Without Towing Package"
- "Heavy Duty Suspension"
- "4-Wheel ABS"

#### 🏷️ Brand Table
**Purpose:** AAIA Brand IDs for manufacturer identification

| Metric | Value |
|--------|-------|
| Brands | 28,000+ |
| Update Frequency | Daily |

### Data Exchange Standards

#### ACES (Aftermarket Catalog Exchange Standard)
**Purpose:** Exchange fitment data (which parts fit which vehicles)

```xml
<App action="A" id="1">
  <BaseVehicle id="2771"/>
  <EngineBase id="1234"/>
  <Qty>2</Qty>
  <PartTerminology id="1684"/>  <!-- ACES 5.0 -->
  <PartNumber>BPD-12345</PartNumber>  <!-- ACES 5.0 -->
  <Note>Front axle only</Note>
</App>
```

#### PIES (Product Information Exchange Standard)
**Purpose:** Exchange product information (descriptions, attributes, pricing)

```xml
<Item>
  <PartNumber>BPD-12345</PartNumber>
  <BrandID>BBBB</BrandID>  <!-- PIES 8.0 -->
  <Description>Premium Ceramic Brake Pads</Description>
  <Prices>
    <Price priceType="JBR">45.99</Price>
  </Prices>
  <ProductAttributes>
    <ProductAttribute>
      <PADBAttribute>Material</PADBAttribute>
      <Value>Ceramic</Value>
    </ProductAttribute>
  </ProductAttributes>
</Item>
```

### How Standards Reference Each Other

The exchange standards (ACES, PIES) reference the databases (VCdb, PCdb, PAdb, Qdb, Brand Table) by ID:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ACES (Fitment Data)                                       │
│                                                                              │
│  <App id="1">                                                                │
│    <BaseVehicle id="2771"/>        ──────────────────► VCdb.BaseVehicle     │
│    <EngineBase id="1234"/>         ──────────────────► VCdb.EngineBase      │
│    <PartTerminology id="1684"/>    ──────────────────► PCdb.PartTerminology │
│    <Qual id="26"/>                 ──────────────────► Qdb.Qualifier        │
│    <PartNumber BrandID="BBBB">     ──────────────────► Brand Table          │
│  </App>                                                                      │
│                                                                              │
│  References: VCdb, PCdb, Qdb, Brand Table                                   │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIES (Product Data)                                       │
│                                                                              │
│  <Item>                                                                      │
│    <BrandID>BBBB</BrandID>         ──────────────────► Brand Table          │
│    <PartTerminologyID>1684</...>   ──────────────────► PCdb.PartTerminology │
│    <ProductAttributes>                                                       │
│      <PADBAttribute id="123"/>     ──────────────────► PAdb.PartAttributes  │
│      <Value>Ceramic</Value>        ──────────────────► PAdb.ValidValues     │
│    </ProductAttributes>                                                      │
│  </Item>                                                                     │
│                                                                              │
│  References: PAdb, PCdb, Brand Table                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Reference Summary

| Exchange Standard | References These Databases | Purpose |
|-------------------|---------------------------|---------|
| **ACES** | VCdb, PCdb, Qdb, Brand Table | "Part X fits Vehicle Y (with qualifier Z)" |
| **PIES** | PAdb, PCdb, Brand Table | "Part X has these attributes and specs" |

| Database | Referenced By | Provides |
|----------|---------------|----------|
| **VCdb** | ACES | Vehicle IDs (BaseVehicle, Engine, Transmission, etc.) |
| **PCdb** | ACES, PIES | Part terminology IDs (what kind of part is this?) |
| **PAdb** | PIES | Attribute definitions and valid values |
| **Qdb** | ACES | Qualifier IDs ("With A/C", "Heavy Duty", etc.) |
| **Brand Table** | ACES, PIES | Brand/manufacturer IDs |

**Think of it this way:**
- **ACES** = "This brake pad fits a 2024 Honda Accord with the 2.0L turbo engine"
- **PIES** = "This brake pad is ceramic, weighs 450g, and costs $45.99"
- Both reference **PCdb** to agree on what "brake pad" means (PartTerminology ID 1684)

---

## 🔄 API Version Comparison

### ACES 4.2 → ACES 5.0 Changes

#### 🔴 Breaking Changes (Must Update)

| Change | ACES 4.2 | ACES 5.0 | Impact |
|--------|----------|----------|--------|
| Element | `<Part>` | `<PartNumber>` | All XML parsers must update |
| Element | `<PartType>` | `<PartTerminology>` | Semantic change - references PCdb |
| Attribute | `BrandAAIAID` | `BrandID` | Header & part elements |
| Attribute | `SubBrandAAIAID` | `SubBrandID` | Header & part elements |
| Header | `VcdbVersionDate` | `VCdbPublicationDate` | Header parsing |
| Header | `QdbVersionDate` | `QdbPublicationDate` | Header parsing |
| Header | `PcdbVersionDate` | `PCdbPublicationDate` | Header parsing |

#### 🟡 Structural Changes

**Asset Reference Restructuring (Rev 3):**
```xml
<!-- ACES 4.2 - OLD -->
<References>
  <DiagramReference>
    <AssetReference>...</AssetReference>
  </DiagramReference>
</References>

<!-- ACES 5.0 - NEW -->
<DiagramAsset>...</DiagramAsset>
<NonDiagramAssets>
  <NonDiagramAsset>...</NonDiagramAsset>
</NonDiagramAssets>
```

**PartNumber Validation Stricter:**
- Minimum length: 1 (was 0)
- Disallowed characters: `;][}{~|,%!$*^\?'"`

**MfrLabel Now Multiple:**
```xml
<!-- ACES 4.2: Single label -->
<MfrLabel>OEM Label</MfrLabel>

<!-- ACES 5.0: Multiple labels supported -->
<MfrLabel>OEM Label 1</MfrLabel>
<MfrLabel>OEM Label 2</MfrLabel>
```

### PIES 7.2 → PIES 8.0 Changes

#### 🟢 New Features (Additive)

**Packaging Items Segment (New in 8.0):**
```xml
<PackagingItems>
  <PackagingItem>
    <PackagingItemLevel>1</PackagingItemLevel>
    <PackagingItemQuantity>1</PackagingItemQuantity>
    <PackagingItemCategory>Box</PackagingItemCategory>
    <PackagingItemDescription>Retail Box</PackagingItemDescription>
    <PackagingItemMaterialCategory>Cardboard</PackagingItemMaterialCategory>
    <PackagingItemDimensions>
      <Height UOM="IN">4.5</Height>
      <Length UOM="IN">8.0</Length>
      <Width UOM="IN">6.0</Width>
    </PackagingItemDimensions>
    <PackagingItemWeight UOM="LB">0.2</PackagingItemWeight>
  </PackagingItem>
</PackagingItems>
```

**New Types Added:**
- `WeightType` - Standardized weight element type
- `LanguageCodeType` - ISO language code validation

#### 🟢 Backward Compatibility

PIES 8.0 **maintains all existing reference numbers** from PIES 7.2. Existing parsers will continue to work, but new packaging data will be ignored unless explicitly handled.

### VCdb 1.0 → VCdb 2.0 Changes

*Detailed field-level changes documented in Excel files. Key areas:*

- Publication date field standardization
- New vehicle configuration attributes
- Enhanced EV (Electric Vehicle) support
- Region handling improvements

### PAdb 4.0 → PAdb 5.0 Changes

*6-year gap between major versions (4.0: Feb 2020, 5.0: Jan 2026)*

- New attributes for modern vehicles
- Enhanced attribute associations
- Improved data rules and validation

---

## 🗄️ Current Database Schema Analysis

### Transtar's Auto Care Implementation

Your SQL Server implementation follows best practices with some clever optimizations:

#### TransendData.VCDB Schema

```sql
-- BaseVehicle: 49,206 rows
┌────────────────────────────────────────────────────────────┐
│ BaseVehicleID (PK) │ YearID │ MakeID │ MakeName │ ModelID │
│ ModelName │ VHID3 (hierarchyid) │ RegionIDBitmap         │
└────────────────────────────────────────────────────────────┘

-- Vehicle: 109,520 rows (BaseVehicle + SubModel)
┌─────────────────────────────────────────────────────────────┐
│ YearID │ MakeID │ MakeName │ ModelID │ ModelName │          │
│ SubModelID │ SubModelName │ BaseVehicleID │ VHID │ EVBitmap │
└─────────────────────────────────────────────────────────────┘

-- Engine: 11,902 configurations
┌───────────────────────────────────────────────────────────────┐
│ EngineConfigID (PK) │ Liter │ BlockType │ Cylinders │         │
│ AspirationID/Name │ FuelTypeID/Name │ PowerOutputID │         │
│ HorsePower │ KilowattPower │ EngineDesignationID/Name │       │
│ EngineMfrID/Name │ EngineVINID/Name │ VHID │ EngineLabel     │
└───────────────────────────────────────────────────────────────┘
```

#### 🌟 Clever Design: HIERARCHYID for Fitment

Your use of SQL Server's `hierarchyid` type is excellent for fitment lookups:

```
Vehicle VHID: /1/2/3/4/5/6/7/  (7-level: Year/Make/Model/SubModel/Engine/Trans/Drive)
Fitment VHID: /1/2/3/          (3-level: Year/Make/Model - covers all submodels)

Lookup: WHERE Vehicle.VHID.IsDescendantOf(Fitment.VHID) = 1
```

This allows **hierarchical matching** - a fitment at Year/Make/Model level automatically applies to all SubModel variants beneath it.

#### TransendFitment Schema

```sql
-- Product.ItemFitment: 17,390,531 rows
┌────────────────────────────────────────────────────────────────┐
│ ItemID │ MinVHID │ MaxVHID │ YearStart │ YearEnd │             │
│ DriveTypeIDBIN │ MakeID │ ModelID │ TransmissionMfrCodeID     │
└────────────────────────────────────────────────────────────────┘

-- PIES.Attribute: 3,637 attributes
┌──────────────────────────────────────────────────────────────┐
│ AttributeID (PK) │ AttributeName │ SortWeight │ Filter │     │
│ ValueCount                                                   │
└──────────────────────────────────────────────────────────────┘

-- PIES.ItemAttributeValue: 3,487,139 rows
┌─────────────────────────────────────────────────────────────┐
│ ItemID │ AttributeID │ Attribute │ AttributeTextOnly        │
└─────────────────────────────────────────────────────────────┘
```

### Data Volumes Summary

| Database | Table | Rows |
|----------|-------|------|
| TransendData | VCDB.BaseVehicle | 49,206 |
| TransendData | VCDB.Vehicle | 109,520 |
| TransendData | VCDB.Engine | 11,902 |
| TransendData | Product.VehicleItemFilter | 4,291,718 |
| TransendFitment | Product.ItemFitment | 17,390,531 |
| TransendFitment | Product.ItemGroup | 184,184,832 |
| TransendFitment | PIES.ItemAttributeValue | 3,487,139 |

---

## ⚠️ Breaking Changes & Deprecations

### Priority 1: Immediate Action Required

#### PIES 8.0 (Already Effective: 10/2/2025)

**Status:** 🔴 **4 months overdue for migration**

**Required Changes:**
1. Add support for `PackagingItems` segment (optional but recommended)
2. Update weight field handling to new `WeightType`
3. Add `LanguageCodeType` validation

**Risk:** Low - PIES 8.0 is backward compatible. Existing data continues to work.

### Priority 2: Plan for January 2026

#### ACES 5.0 Breaking Changes

| Field | Action Required | Code Impact |
|-------|-----------------|-------------|
| `Part` → `PartNumber` | Update XML parsing | High - all extraction logic |
| `PartType` → `PartTerminology` | Update XML parsing + semantics | High |
| `BrandAAIAID` → `BrandID` | Update XML parsing | Medium |
| `*VersionDate` → `*PublicationDate` | Update header parsing | Low |
| Asset references | Complete rewrite | High - if using digital assets |

#### VCdb 2.0 Changes

Review `VCdb_2_0_TableAndFieldDefinitions_Rev2_1_28_2026.xlsx` for:
- Field renames
- New tables
- Deprecated fields

#### PAdb 5.0 Changes

Review `PAdb_5_0_TableAndFieldDefinitions_Rev3_1_28_2026.xlsx` for:
- New attributes
- Changed associations
- Validation rules

### Deprecation Mapping: Your Database vs New API

| Your Field | Status | New API Field | Action |
|------------|--------|---------------|--------|
| `VCDB.Engine.VHID` | ✅ OK | Same concept | None |
| `PIES.Attribute.*` | ✅ OK | Compatible | None |
| Header version dates | 🟡 Rename | `*PublicationDate` | Update parsers |
| Asset references | 🔴 Restructured | New structure | Rewrite if used |

---

## 🏗️ Architecture Recommendations

### Data Ingestion Options Analysis

You asked about **Option A (Fivetran Function)** vs **Option C (Full Dagster)**. Here's the analysis:

### Option A: Fivetran Function Connector

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OPTION A: Fivetran Function                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Auto Care VIP API                                                      │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────┐                                                   │
│  │  AWS Lambda     │  ◄── Wraps autocare-python                        │
│  │  (Python 3.13)  │                                                   │
│  └────────┬────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐  │
│  │    Fivetran     │────►│    Snowflake    │────►│     Dagster     │  │
│  │  Function Conn  │     │   (RAW layer)   │     │  (transforms)   │  │
│  └─────────────────┘     └─────────────────┘     └─────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Fivetran handles scheduling, retries, monitoring
- ✅ Built-in incremental sync tracking
- ✅ Centralized data movement in one tool
- ✅ Schema drift detection
- ✅ Fivetran dashboard for non-technical users

**Cons:**
- ❌ Additional Lambda infrastructure to maintain
- ❌ Cold start latency for Lambda
- ❌ Fivetran Function connector requires Business tier ($$$)
- ❌ Limited control over API pagination/rate limiting
- ❌ Debugging spans multiple systems

**Cost Estimate:**
- Fivetran Business: ~$2,000/mo base + MAR charges
- Lambda: ~$50/mo (minimal usage)
- Total: ~$2,000-3,000/mo

### Option C: Full Dagster

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        OPTION C: Full Dagster                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Auto Care VIP API                                                      │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        Dagster Cloud                             │   │
│  │  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │   │
│  │  │  API Asset  │────►│  RAW Asset  │────►│ MART Asset  │       │   │
│  │  │  (extract)  │     │  (load)     │     │ (transform) │       │   │
│  │  └─────────────┘     └─────────────┘     └─────────────┘       │   │
│  │        │                    │                    │              │   │
│  │        └────────────────────┴────────────────────┘              │   │
│  │                             │                                   │   │
│  │                             ▼                                   │   │
│  │                      ┌─────────────┐                           │   │
│  │                      │  Snowflake  │                           │   │
│  │                      └─────────────┘                           │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Pros:**
- ✅ Single system for all data operations
- ✅ Full control over API interaction
- ✅ Direct use of autocare-python library
- ✅ Software-defined assets with lineage
- ✅ Better debugging (single system)
- ✅ Partitioning by date/database
- ✅ Dagster Cloud Serverless = low ops burden

**Cons:**
- ❌ More custom code to maintain
- ❌ Must implement retry/backoff logic
- ❌ Must track incremental sync state yourself
- ❌ Dagster learning curve

**Cost Estimate:**
- Dagster Cloud Serverless: ~$400/mo (based on compute)
- Total: ~$400-600/mo

### 🏆 Recommendation: Option C (Full Dagster)

**Rationale:**
1. **Cost:** 5x cheaper than Fivetran
2. **Control:** Direct API integration with autocare-python
3. **Existing Investment:** You already have dagster-poc with Snowflake + Elasticsearch
4. **Consistency:** Single tool for Extract + Transform + Load
5. **Visibility:** Software-defined assets provide clear lineage

### Alternative ETL Tools Considered

| Tool | Fit for Auto Care API | Notes |
|------|----------------------|-------|
| **Airbyte** | ⚠️ No native connector | Would need custom connector (similar effort to Dagster) |
| **Meltano** | ⚠️ No native connector | Singer tap would need to be built |
| **dlt (data load tool)** | ✅ Good fit | Lightweight, could complement Dagster |
| **Prefect** | ✅ Good fit | Similar to Dagster, less asset-focused |
| **Apache Airflow** | ⚠️ Overkill | More ops burden, DAG-focused not asset-focused |

**dlt** is worth considering as a lightweight extraction layer within Dagster assets.

---

## ☁️ AWS Database Migration Options

You mentioned wanting to move off on-prem SQL Server. Here's the analysis:

### Option 1: Amazon Aurora PostgreSQL

```
┌──────────────────────────────────────────────────────────────┐
│                   AURORA POSTGRESQL                           │
├──────────────────────────────────────────────────────────────┤
│  ✅ Pros                      │  ❌ Cons                      │
│  • PostgreSQL compatibility   │  • No native hierarchyid     │
│  • Serverless v2 option       │  • VHID migration required   │
│  • Read replicas              │  • Some SQL Server syntax    │
│  • Auto-scaling storage       │    differences               │
│  • pgvector for embeddings    │                              │
├──────────────────────────────────────────────────────────────┤
│  💰 Cost: ~$200-800/mo (serverless, auto-scales)             │
│  🔧 Migration: Medium effort (hierarchyid → ltree)           │
└──────────────────────────────────────────────────────────────┘
```

**hierarchyid Migration Strategy:**
```sql
-- SQL Server
VHID hierarchyid = '/1/2/3/4/5/'

-- PostgreSQL with ltree extension
CREATE EXTENSION ltree;
vhid ltree = '1.2.3.4.5';

-- Query: IsDescendantOf equivalent
WHERE vhid <@ '1.2.3';  -- All descendants of /1/2/3/
```

### Option 2: Amazon Aurora MySQL

```
┌──────────────────────────────────────────────────────────────┐
│                     AURORA MYSQL                              │
├──────────────────────────────────────────────────────────────┤
│  ✅ Pros                      │  ❌ Cons                      │
│  • Familiar SQL syntax        │  • No native hierarchyid     │
│  • Serverless v2 option       │  • No ltree equivalent       │
│  • Read replicas              │  • Less mature JSON support  │
│  • Wide tooling support       │                              │
├──────────────────────────────────────────────────────────────┤
│  💰 Cost: ~$200-800/mo (serverless)                          │
│  🔧 Migration: Medium-High (path encoding workaround)        │
└──────────────────────────────────────────────────────────────┘
```

### Option 3: Amazon RDS SQL Server

```
┌──────────────────────────────────────────────────────────────┐
│                   RDS SQL SERVER                              │
├──────────────────────────────────────────────────────────────┤
│  ✅ Pros                      │  ❌ Cons                      │
│  • Zero code changes          │  • SQL Server licensing      │
│  • Native hierarchyid         │  • Higher cost               │
│  • Lift-and-shift             │  • Less cloud-native         │
│  • Multi-AZ available         │                              │
├──────────────────────────────────────────────────────────────┤
│  💰 Cost: ~$500-2000/mo (includes license)                   │
│  🔧 Migration: Low effort (backup/restore)                   │
└──────────────────────────────────────────────────────────────┘
```

### Option 4: Snowflake (Data Warehouse)

```
┌──────────────────────────────────────────────────────────────┐
│                      SNOWFLAKE                                │
├──────────────────────────────────────────────────────────────┤
│  ✅ Pros                      │  ❌ Cons                      │
│  • Already in your stack      │  • Not ideal for OLTP        │
│  • Separation of compute      │  • No hierarchyid            │
│  • Excellent for analytics    │  • Query latency for apps    │
│  • Native JSON support        │  • Cost per query            │
├──────────────────────────────────────────────────────────────┤
│  💰 Cost: Pay-per-query (~$2-4/credit)                       │
│  🔧 Migration: Medium (schema adaptation)                    │
└──────────────────────────────────────────────────────────────┘
```

### 🏆 Recommendation: Aurora PostgreSQL + Fivetran + Snowflake

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RECOMMENDED ARCHITECTURE                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Auto Care VIP API                                                      │
│       │                                                                 │
│       ▼                                                                 │
│  ┌─────────────────┐                                                   │
│  │     Dagster     │  Extract + Transform                              │
│  └────────┬────────┘                                                   │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐  │
│  │ Aurora Postgres │────▶│    Fivetran     │────▶│    Snowflake    │  │
│  │ (source of truth)     │   (CDC sync)    │     │   (analytics)   │  │
│  └────────┬────────┘     └─────────────────┘     └─────────────────┘  │
│           │                                                             │
│           ▼                                                             │
│  ┌─────────────────┐                                                   │
│  │  Application    │  Low-latency queries                              │
│  │     APIs        │                                                   │
│  └─────────────────┘                                                   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

**Why This Architecture:**

| Factor | Benefit |
|--------|---------|
| **Single write target** | Dagster only writes to Aurora (simpler pipeline) |
| **Fivetran strength** | Database replication via CDC is what Fivetran does best |
| **Native connector** | Fivetran has native PostgreSQL connector (no Lambda needed) |
| **Source of truth** | Aurora is the single source - Snowflake is a replica |
| **Existing stack** | Leverages Fivetran you already have |
| **Cost efficient** | PostgreSQL connector is cheaper than Function connector |

**Data Flow:**
1. **Dagster** extracts from Auto Care API, transforms, loads to Aurora PostgreSQL
2. **Aurora PostgreSQL** serves as operational database (low-latency app queries)
3. **Fivetran** replicates Aurora → Snowflake via CDC (5-15 min latency)
4. **Snowflake** serves analytics, BI, data science workloads

**Rationale:**
1. **Aurora PostgreSQL** as source of truth for operational workloads
2. **ltree extension** provides hierarchyid-like functionality for fitment queries
3. **Serverless v2** scales to zero when not in use
4. **Fivetran CDC** efficiently syncs changes to Snowflake for analytics
5. **Snowflake** handles heavy analytical queries without impacting operational DB

---

## 🔄 Dagster Ingestion Design

### IO Manager Configuration

All assets write to **Aurora PostgreSQL only**. Fivetran handles replication to Snowflake.

```python
# definitions.py

from dagster import Definitions
from dagster_postgres import PostgresIOManager

defs = Definitions(
    assets=[...],
    resources={
        "io_manager": PostgresIOManager(
            host=os.environ["AURORA_HOST"],
            port=5432,
            database="autocare",
            user=os.environ["AURORA_USER"],
            password=os.environ["AURORA_PASSWORD"],
        ),
    },
)
```

### Asset Hierarchy

```python
# autocare_assets.py

from dagster import asset, AssetExecutionContext, DailyPartitionsDefinition
from autocare import AutoCareAPI

daily_partitions = DailyPartitionsDefinition(start_date="2026-01-01")

@asset(
    partitions_def=daily_partitions,
    group_name="autocare_raw",
    description="Raw VCdb data from Auto Care API"
)
def raw_vcdb_vehicles(context: AssetExecutionContext) -> pd.DataFrame:
    """Extract vehicle data from VCdb API."""
    with AutoCareAPI(
        username=os.environ["AUTOCARE_USERNAME"],
        password=os.environ["AUTOCARE_PASSWORD"],
        client_id=os.environ["AUTOCARE_CLIENT_ID"],
        client_secret=os.environ["AUTOCARE_CLIENT_SECRET"],
    ) as client:
        records = list(client.fetch_all_records("vcdb", "Vehicle"))
        return pd.DataFrame(records)

@asset(
    partitions_def=daily_partitions,
    group_name="autocare_raw",
)
def raw_vcdb_engines(context: AssetExecutionContext) -> pd.DataFrame:
    """Extract engine configurations from VCdb API."""
    # Similar pattern...

@asset(
    partitions_def=daily_partitions,
    group_name="autocare_raw",
)
def raw_pcdb_part_terminologies(context: AssetExecutionContext) -> pd.DataFrame:
    """Extract part terminologies from PCdb API."""
    # Similar pattern...

@asset(
    partitions_def=daily_partitions,
    group_name="autocare_raw",
)
def raw_brand_table(context: AssetExecutionContext) -> pd.DataFrame:
    """Extract brand table (daily updates)."""
    # Similar pattern...
```

### Staging Layer

```python
@asset(
    deps=["raw_vcdb_vehicles"],
    group_name="autocare_staging",
)
def stg_vehicles(context: AssetExecutionContext, raw_vcdb_vehicles: pd.DataFrame) -> pd.DataFrame:
    """
    Staged vehicles with:
    - Data type validation
    - NULL handling
    - VHID path generation (for PostgreSQL ltree)
    """
    df = raw_vcdb_vehicles.copy()

    # Generate ltree-compatible path
    df["vhid_path"] = df.apply(
        lambda r: f"{r['YearID']}.{r['MakeID']}.{r['ModelID']}.{r['SubModelID']}",
        axis=1
    )

    return df
```

### Mart Layer

```python
@asset(
    deps=["stg_vehicles", "stg_engines", "stg_transmissions"],
    group_name="autocare_marts",
)
def mart_vehicle_configurations(
    stg_vehicles: pd.DataFrame,
    stg_engines: pd.DataFrame,
    stg_transmissions: pd.DataFrame,
) -> pd.DataFrame:
    """
    Denormalized vehicle configurations for fast lookup.
    Combines vehicle base with engine and transmission options.
    """
    # Join logic...
```

### Incremental Loading Support

Auto Care databases support incremental loading via built-in timestamp fields present in **every table**:

| Field | Purpose | Example |
|-------|---------|---------|
| `EffectiveDateTime` | When record was added/modified | `2026-01-13T01:53:17.383` |
| `EndDateTime` | When record was deleted (null = active) | `null` or `2026-01-13T01:23:24.3` |
| `WhenModified` | Explicit modification timestamp (ChangeLog) | `2026-01-13T01:53:17.383` |

**Record State Logic:**
```
Added/Modified: EffectiveDateTime = populated, EndDateTime = null
Deleted:        EffectiveDateTime = populated, EndDateTime = populated
Active:         EndDateTime = null
```

**Sample VCdb Vehicle Record:**
```json
{
  "VehicleID": 55619,
  "BaseVehicleID": 18253,
  "SubmodelID": 296,
  "RegionID": 1,
  "PublicationStageID": 4,
  "EffectiveDateTime": "2017-04-21T13:21:29",
  "EndDateTime": null
}
```

### Sensor for Publication Detection

The sensor checks for new Auto Care publications by querying the `Version` table:

```python
from dagster import sensor, RunRequest, SensorEvaluationContext

@sensor(
    job=autocare_daily_sync_job,
    minimum_interval_seconds=3600,  # Check hourly
)
def autocare_publication_sensor(context: SensorEvaluationContext):
    """
    Trigger sync when Auto Care publishes new data.
    Checks Version table for new PublicationDate.
    """
    with AutoCareAPI(...) as client:
        # Get current publication date from Version endpoint
        version_info = list(client.fetch_records("vcdb", "Version"))
        current_pub_date = version_info[0]["PublicationDate"]

    last_synced_pub = context.cursor

    if current_pub_date != last_synced_pub:
        yield RunRequest(
            run_key=current_pub_date,
            run_config={
                "ops": {
                    "raw_vcdb_vehicles": {
                        "config": {"since_date": last_synced_pub}
                    }
                }
            }
        )
        context.update_cursor(current_pub_date)
```

### Incremental Asset Pattern

Assets filter records by `EffectiveDateTime` to only process new/modified data:

```python
@asset(group_name="autocare_raw")
def raw_vcdb_vehicles(context: AssetExecutionContext) -> pd.DataFrame:
    """
    Extract vehicle data with incremental loading.
    Only fetches records modified since last sync.
    """
    since_date = context.op_config.get("since_date")

    with AutoCareAPI(...) as client:
        all_records = list(client.fetch_all_records("vcdb", "Vehicle"))

    df = pd.DataFrame(all_records)

    if since_date:
        # Incremental: filter to new/modified records
        df = df[df["EffectiveDateTime"] > since_date]
        context.log.info(f"Incremental load: {len(df)} records since {since_date}")
    else:
        # Initial load: all records
        context.log.info(f"Full load: {len(df)} records")

    return df
```

### Handling Deletes

Soft deletes are identified by `EndDateTime` being populated:

```python
@asset(deps=["raw_vcdb_vehicles"])
def staged_vcdb_vehicles(raw_vcdb_vehicles: pd.DataFrame) -> None:
    """
    Merge into Aurora with proper handling of deletes.
    """
    engine = create_engine(os.environ["AURORA_URL"])

    # Separate active vs deleted records
    active_records = raw_vcdb_vehicles[raw_vcdb_vehicles["EndDateTime"].isna()]
    deleted_records = raw_vcdb_vehicles[raw_vcdb_vehicles["EndDateTime"].notna()]

    # Upsert active records
    active_records.to_sql("vcdb_vehicles_staging", engine, if_exists="replace")
    engine.execute("""
        INSERT INTO vcdb_vehicles (vehicle_id, base_vehicle_id, ...)
        SELECT vehicle_id, base_vehicle_id, ...
        FROM vcdb_vehicles_staging
        ON CONFLICT (vehicle_id) DO UPDATE SET
            base_vehicle_id = EXCLUDED.base_vehicle_id,
            effective_date_time = EXCLUDED.effective_date_time,
            updated_at = NOW()
    """)

    # Soft delete removed records
    if len(deleted_records) > 0:
        deleted_ids = deleted_records["VehicleID"].tolist()
        engine.execute(f"""
            UPDATE vcdb_vehicles
            SET end_date_time = NOW(), is_active = FALSE
            WHERE vehicle_id IN ({','.join(map(str, deleted_ids))})
        """)
```

### ChangeLog Files (Manual Download Only)

Auto Care provides ChangeLog files containing only changed records between publications:

```
Available at: AutoCareVIP.com > Downloads > [Database] > ChangeLog
Formats: JSON, ASCII
Contains: Only Added/Modified/Deleted records for the publication period
```

**⚠️ Important:** ChangeLog files are **manual download only** - no API endpoint exists for programmatic access.

### Why You Don't Need ChangeLog Files

Since every API table includes `EffectiveDateTime` and `EndDateTime`, the **recommended approach** is:

1. **Fetch all records** via API (full table)
2. **Filter locally** by `EffectiveDateTime > last_sync_date`
3. **UPSERT** into Aurora PostgreSQL

**This is efficient enough for daily sync:**

| Database | Typical Records | Fetch Time |
|----------|-----------------|------------|
| VCdb Vehicle | ~110,000 | ~30 sec |
| VCdb Engine | ~12,000 | ~5 sec |
| VCdb BaseVehicle | ~50,000 | ~15 sec |
| Brand Table | ~28,000 | ~10 sec |
| PAdb Attributes | ~10,000 | ~5 sec |

**Total daily sync: ~2-3 minutes** for all databases, which is acceptable for a daily batch job.

### Future Optimization

Once you have API credentials, test if the API supports query filtering:

```python
# Test these patterns with real credentials
params = {"effectiveDateTime.gt": "2026-02-01"}
params = {"$filter": "EffectiveDateTime gt 2026-02-01"}
params = {"modifiedSince": "2026-02-01"}
```

If native filtering is supported, you can skip fetching unchanged records entirely.

---

## 🐍 autocare-python Update Plan

### Current State (v0.1.0)

The autocare-python library is well-architected with:
- ✅ OAuth2 authentication with auto-refresh
- ✅ Retry logic (429, 5xx errors)
- ✅ Pagination support
- ✅ Type hints and dataclasses
- ✅ Comprehensive test suite

### Required Updates for New API Versions

#### Phase 1: Multi-Version Support

```python
# Current (v0.1.0)
client = AutoCareAPI(...)
client.fetch_records("vcdb", "Vehicle")  # Always v1.0

# Proposed (v0.2.0)
client = AutoCareAPI(
    ...,
    api_versions={
        "vcdb": "2.0",
        "pcdb": "1.0",  # PCdb not changing
        "aces": "5.0",
        "pies": "8.0",
    }
)
```

#### Phase 2: Database-Specific Modules

```
autocare/
├── __init__.py
├── client.py          # Core client (existing)
├── vcdb/
│   ├── __init__.py
│   ├── v1.py          # VCdb 1.0 models
│   └── v2.py          # VCdb 2.0 models
├── pcdb/
│   └── ...
├── aces/
│   ├── v4.py          # ACES 4.2 parser
│   └── v5.py          # ACES 5.0 parser
├── pies/
│   ├── v7.py          # PIES 7.2 parser
│   └── v8.py          # PIES 8.0 parser
└── compatibility/
    └── field_mapping.py  # v1→v2 field name mapping
```

#### Phase 3: Field Mapping Layer

```python
# autocare/compatibility/field_mapping.py

ACES_4_TO_5_MAPPING = {
    "Part": "PartNumber",
    "PartType": "PartTerminology",
    "BrandAAIAID": "BrandID",
    "SubBrandAAIAID": "SubBrandID",
    "VcdbVersionDate": "VCdbPublicationDate",
    "QdbVersionDate": "QdbPublicationDate",
    "PcdbVersionDate": "PCdbPublicationDate",
}

def migrate_aces_record(record: dict, from_version="4.2", to_version="5.0") -> dict:
    """Translate ACES record field names between versions."""
    if from_version == "4.2" and to_version == "5.0":
        return {ACES_4_TO_5_MAPPING.get(k, k): v for k, v in record.items()}
    return record
```

### Proposed Changelog

```markdown
## [0.2.0] - 2026-03-01

### Added
- Multi-version API support via `api_versions` parameter
- VCdb 2.0 support
- PAdb 5.0 support
- ACES 5.0 parser with new element names
- PIES 8.0 parser with PackagingItems support
- Field mapping utilities for version migration
- New database-specific submodules

### Changed
- Default API versions updated to latest stable
- Improved error messages for version mismatches

### Deprecated
- Direct table name strings (use database-specific modules)
```

---

## 📅 Implementation Roadmap

### Phase 1: Immediate (February 2026)

**Focus:** PIES 8.0 compatibility (already overdue)

| Task | Owner | Status |
|------|-------|--------|
| Add PIES 8.0 PackagingItems parsing | Dev | 🔲 |
| Update PIES schema validation | Dev | 🔲 |
| Test with existing data | QA | 🔲 |

### Phase 2: Q1 2026 (March-April)

**Focus:** autocare-python v0.2.0

| Task | Owner | Status |
|------|-------|--------|
| Implement multi-version support | Dev | 🔲 |
| Add VCdb 2.0 module | Dev | 🔲 |
| Add ACES 5.0 parser | Dev | 🔲 |
| Field mapping utilities | Dev | 🔲 |
| Update test suite | QA | 🔲 |
| Release v0.2.0 | DevOps | 🔲 |

### Phase 3: Q2-Q3 2026 (May-August)

**Focus:** Aurora PostgreSQL migration + Dagster ingestion pipeline

*Aurora must be provisioned first since Dagster writes directly to it.*

| Task | Owner | Status |
|------|-------|--------|
| **AWS Infrastructure** | | |
| Provision Aurora PostgreSQL Serverless v2 | DevOps | 🔲 |
| Configure ltree extension for VHID paths | DBA | 🔲 |
| Set up Fivetran PostgreSQL → Snowflake connector | DevOps | 🔲 |
| **Dagster Pipeline** | | |
| Design asset hierarchy | Data Eng | 🔲 |
| Implement raw layer assets | Data Eng | 🔲 |
| Implement staging layer | Data Eng | 🔲 |
| Implement mart layer | Data Eng | 🔲 |
| Publication detection sensor | Data Eng | 🔲 |
| Deploy to Dagster Cloud | DevOps | 🔲 |
| **Migration & Cutover** | | |
| Migrate existing VCDB data to Aurora | DBA | 🔲 |
| Update application connection strings | Dev | 🔲 |
| Performance testing | QA | 🔲 |
| Decommission on-prem SQL Server | DevOps | 🔲 |

### Phase 4: Q4 2026 (September-October)

**Focus:** Documentation, training & ACES 5.0/VCdb 2.0/PAdb 5.0 cutover

| Task | Owner | Status |
|------|-------|--------|
| **Documentation** | | |
| Complete onboarding documentation | Tech Writer | 🔲 |
| Migrate docs to Confluence | Tech Writer | 🔲 |
| **Training** | | |
| Conduct training sessions | Team Lead | 🔲 |
| Knowledge transfer | All | 🔲 |
| **January 2026 Version Cutover** | | |
| Enable ACES 5.0 parsing | Dev | 🔲 |
| Enable VCdb 2.0 ingestion | Dev | 🔲 |
| Enable PAdb 5.0 ingestion | Dev | 🔲 |
| Validate data integrity post-cutover | QA | 🔲 |

---

## 📎 Appendix

### File References

| Document | Location |
|----------|----------|
| ACES 5.0 XSD | `docs/autocare-api/ACES_5_0_Documentation_1_28_2026/ACES_5_0_XSDSchema_Rev3_1_28_2026.xsd` |
| PIES 8.0 XSD | `docs/autocare-api/PIES_8_0_Documentation_10_2_2025/PIES_8_0_XSDSchema_Rev3_10_2_2025.xsd` |
| VCdb 2.0 Fields | `docs/autocare-api/VCdb_2_0_Documentation_1_28_2026/VCdb_2_0_TableAndFieldDefinitions_Rev2_1_28_2026.xlsx` |
| PAdb 5.0 Fields | `docs/autocare-api/PAdb_5_0_Documentation_1_28_2026/PAdb_5_0_TableAndFieldDefinitions_Rev3_1_28_2026.xlsx` |
| API Usage Guide | `docs/autocare-api/Reference Database API_Usage Guide_Rev3_3_11_2025.pdf` |

### Related Repositories

| Repository | Purpose |
|------------|---------|
| `TranstarIndustries/autocare-python` | Auto Care API client library |
| `TranstarIndustries/dagster-poc` | Dagster pipeline implementation |

---

*Document generated by Claude Code analysis of Auto Care Association documentation and Transtar Industries database schema.*
