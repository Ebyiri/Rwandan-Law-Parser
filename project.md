You are an elite systems architect and compiler engineer. I am building a deterministic, AI-free, lightweight, and blazingly fast parser for Rwandan legal PDFs. We are building a compiler that treats a PDF as source code and outputs a strictly validated JSON AST.

We will use Python (PyMuPDF) for extraction, and Zig for the heavy graph-building, regex state machine, and sorting logic. Zig will be compiled to a shared library and called via Python ctypes.

Here is the complete, strict architectural specification and JSON schema for the project. You must write the code to fulfill this exact specification.

### LAYER 0: PDF Canonicalization (Python/PyMuPDF)
- Extract spans via `fitz`. Flip Y-axis so `y0 = page_height - bbox[3]`. Top of page = 0.
- Merge adjacent spans on the same line (`abs(y0_diff) < 2.0`, `x_gap < 2.0`, same font).
- DETERMINISTIC SORT: `sort key = (page, y0, x0)`.
- Split Portrait pages (Metadata) from Landscape pages (Law Body).

### LAYER 1: Column Stream Assembly (Python)
- Use KMeans(n_clusters=3, random_state=42) on `x0` coords of Landscape blocks to find 3 columns (RW, EN, FR).
- DO NOT parse left-to-right. Assemble 3 independent vertical streams sorted by `(page, y0, x0)`. Text flows top-to-bottom within a column, crossing pages.

### LAYER 2: Zig Core - The Graph & State Machine (Zig compiled to .so)
- Write a Zig program `parser_core.zig` exposed via `export fn build_ast(...)`.
- Input: A flat array of blocks from ONE stream (e.g., EN).
- Logic:
  1. Dynamic Font Profiling: Find most frequent `font_size` = `body_size`.
  2. Spatial Constraints: Ignore running headers containing 'Official Gazette' and bottom-margin page numbers. Implement ToC Rejection: If an Article/Chapter regex matches in the top 30% Y-coordinate zone of early pages, reject it as TOC.
  3. Apply the following exact Regex grammar (RLRC 2022 compliant) to classify nodes:
     - PART: `^PART\s+(ONE|TWO|...|\d+)`
     - TITLE: `^TITLE\s+(ONE|TWO|...|\d+)`
     - CHAPTER: `^CHAPTER\s+(ONE|TWO|...|\d+)`
     - SECTION: `^Section\s+(One|...|\d+)`
     - SUBSECTION: `^Subsection\s+(One|...|\d+)`
     - ARTICLE: `^Article\s+(One|First|\d+)(\s+(bis|ter|quater|quinquies))?` (Must capture amendment numbers).
  4. Hierarchy: Maintain a stack. Larger fonts push to higher divisions. Indentation (`x0 > parent.x0 + 15`) creates child nodes (lists/subparagraphs).
- Output: An array of C-compatible structs: `{id, parent_id, node_type, number, y0, source_block_ids_array, source_block_ids_len}`.

### LAYER 3: Fuzzy Trilingual Merge (Python)
- Parse RW, EN, FR streams independently into 3 ASTs via the Zig core.
- Use `ast_en` as master skeleton. Match RW/FR nodes by Regex Number (Primary) or Fuzzy Y-coordinate proximity ±15px (Secondary fallback for translations like "Article premier" vs "Article 1").

### LAYER 4: JSON Builder & Validation (Python)
- Serialize the merged AST into the strict JSON schema provided below.
- EVERY node must include `"source_blocks": [id1, id2...]` for traceability.
- Enforce the Block Conservation Law: `Total Input Blocks == Assigned Blocks + Unclassified Blocks`.

### TARGET JSON SCHEMA SPECIFICATION:
```json
{
  "document_metadata_schema": {
    "portrait_pages": {
      "fields": {
        "official_gazette_number": { "type": "string", "extraction_regex": "(?i)Official\\s+Gazette\\s+no\\.\\s*([^\\n]+)" },
        "type_of_the_law": {
          "type": "string",
          "enum": ["Constitution", "Organic Law", "Ordinary Law", "International Treaty", "Presidential Order", "Ministerial Order", "Decree Law", "Rules and Regulation"],
          "classification_rules": {
            "Kinyarwanda_keywords": {"Itegeko Nshinga": "Constitution", "Itegeko Ngenga": "Organic Law", "Itegeko": "Ordinary Law", "Iteka rya Perezida": "Presidential Order", "Iteka rya Minisitiri": "Ministerial Order"},
            "French_keywords": {"Loi Constitutionnelle": "Constitution", "Loi Organique": "Organic Law", "Loi": "Ordinary Law", "Arrêté Présidentiel": "Presidential Order", "Arrêté Ministériel": "Ministerial Order"}
          }
        },
        "name_of_the_law": { "type": "object", "properties": { "rw": {"type": "string"}, "en": {"type": "string"}, "fr": {"type": "string"} } }
      }
    }
  },
  "body_of_the_law_schema": {
    "landscape_pages": {
      "parsing_strategy": "Columnar by bounding-box blocks, evaluated TOP-TO-BOTTOM within isolated vertical column streams, NOT left-to-right",
      "spatial_constraints": {
        "margin_isolation": "Ignore running headers containing 'Official Gazette' and trailing absolute page numbers",
        "buffer_zones": "X-coordinate segment thresholds between trilingual columns",
        "toc_rejection_rule": "Any structural node matching Article/Chapter regex found in the top 30% Y-coordinate zone of pages preceding the enacting formula must be excluded as TOC",
        "indentation_handling": "Detect indentation alignments to maintain paragraph grouping"
      }
    },
    "hierarchical_structural_nodes": {
      "root": { "node_type": "Law", "child_nodes": ["PREAMBLE", "part"], "properties": { "title": {"type": "string"}, "number": {"type": "string"}, "source_blocks": {"type": "array"} } },
      "PREAMBLE": { "node_type": "BlockText", "properties": { "rw": {"type": "string"}, "en": {"type": "string"}, "fr": {"type": "string"}, "source_blocks": {"type": "array"} } },
      "part": {
        "node_type": "StructuralDivision",
        "regex_identifiers": { "rw": "^IGICE CYA MBERE|^IGICE CYA (?:[IVXLCDM]+|\\d+)", "en": "^PART ONE|^PART (?:[IVXLCDM]+|\\d+)", "fr": "^PREMIÈRE PARTIE|^PARTIE (?:[IVXLCDM]+|\\d+)" },
        "properties": { "number": {"type": "string"}, "title": {"type": "object", "properties": {"rw": {"type": "string"}, "en": {"type": "string"}, "fr": {"type": "string"}}}, "source_blocks": {"type": "array"} },
        "child_nodes": ["title"]
      },
      "title": {
        "node_type": "StructuralDivision",
        "regex_identifiers": { "rw": "^INTERURO YA MBERE|^INTERURO YA (?:[IVXLCDM]+|\\d+)", "en": "^TITLE ONE|^TITLE (?:[IVXLCDM]+|\\d+)", "fr": "^TITRE PREMIER|^TITRE (?:[IVXLCDM]+|\\d+)" },
        "properties": { "number": {"type": "string"}, "title": {"type": "object", "properties": {"rw": {"type": "string"}, "en": {"type": "string"}, "fr": {"type": "string"}}}, "source_blocks": {"type": "array"} },
        "child_nodes": ["chapter"]
      },
      "chapter": {
        "node_type": "StructuralDivision",
        "regex_identifiers": { "rw": "^UMUTWE WA MBERE|^UMUTWE WA (?:[IVXLCDM]+|\\d+)", "en": "^CHAPTER ONE|^CHAPTER (?:[IVXLCDM]+|\\d+)", "fr": "^CHAPITRE PREMIER|^CHAPITRE (?:[IVXLCDM]+|\\d+)" },
        "properties": { "number": {"type": "string"}, "title": {"type": "object", "properties": {"rw": {"type": "string"}, "en": {"type": "string"}, "fr": {"type": "string"}}}, "source_blocks": {"type": "array"} },
        "child_nodes": ["section"]
      },
      "section": {
        "node_type": "StructuralDivision",
        "regex_identifiers": { "rw": "^Icyiciro cya mbere|^Icyiciro cya (?:[IVXLCDM]+|\\d+)", "en": "^Section One|^Section (?:[IVXLCDM]+|\\d+)", "fr": "^Section première|^Section (?:[IVXLCDM]+|\\d+)" },
        "properties": { "number": {"type": "string"}, "title": {"type": "object", "properties": {"rw": {"type": "string"}, "en": {"type": "string"}, "fr": {"type": "string"}}}, "source_blocks": {"type": "array"} },
        "child_nodes": ["sub-section", "article"]
      },
      "sub-section": {
        "node_type": "StructuralDivision",
        "regex_identifiers": { "rw": "^Akiciro ka mbere|^Akiciro ka (?:[IVXLCDM]+|\\d+)", "en": "^Subsection One|^Subsection (?:[IVXLCDM]+|\\d+)", "fr": "^Sous-section première|^Sous-section (?:[IVXLCDM]+|\\d+)" },
        "properties": { "number": {"type": "string"}, "title": {"type": "object", "properties": {"rw": {"type": "string"}, "en": {"type": "string"}, "fr": {"type": "string"}}}, "source_blocks": {"type": "array"} },
        "child_nodes": ["article"]
      },
      "article": {
        "node_type": "ContentNode",
        "regex_identifiers": {
          "rw": "^Ingingo ya mbere:|^Ingingo ya (\\d+):",
          "en": "^Article One:|^Article First:|^Article (\\d+)(\\s+(bis|ter|quater|quinquies))?:",
          "fr": "^Article premier:|^Article (\\d+)(\\s+(bis|ter|quater|quinquies))?:"
        },
        "properties": { "number": {"type": "string"}, "title": {"type": "object", "properties": {"rw": {"type": "string"}, "en": {"type": "string"}, "fr": {"type": "string"}}}, "source_blocks": {"type": "array"} },
        "child_nodes": ["content"]
      },
      "content": {
        "node_type": "LeafNode",
        "properties": {
          "paragraph": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "paragraph_number": { "type": "string" },
                "content": {
                  "type": "object",
                  "oneOf": [
                    { "properties": { "text_line": { "type": "string" } } },
                    { "properties": { "numbered_list": { "type": "object", "properties": { "type": { "type": "string", "enum": ["numerical", "alphabetical", "roman"] }, "marker": { "type": "string" }, "items": { "type": "array", "items": { "type": "string" } }, "nested_list": { "type": "array", "items": { "type": "object" } } } } } }
                  ]
                },
                "source_blocks": {"type": "array"}
              }
            }
          }
        }
      }
    }
  }
}