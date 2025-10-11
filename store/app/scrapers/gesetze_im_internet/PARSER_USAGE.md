# German Legal XML Parser - Usage Guide

## Overview

A comprehensive Python parser for the **gii-norm.dtd** format used by gesetze-im-internet.de. The parser uses `lxml` for XML processing and Python dataclasses for structured data representation.

## Components

### Core Parser

- **`app/services/scrapers/xml_parser.py`** - Main parser implementation
  - 10 dataclass models representing the DTD structure
  - Complete parsing logic for all major elements
  - Text extraction with formatting preservation
  - Table and footnote support
  - Dictionary conversion for JSON serialization

### Documentation

- **`app/services/scrapers/README_PARSER.md`** - Comprehensive documentation with examples
- **`PARSER_USAGE.md`** - This file (usage guide)

### Examples & Tests

- **`examples/parse_example.py`** - Detailed example script showing all features
- **`tests/test_xml_parser.py`** - Complete pytest test suite with 15 tests
- **`test_parser_standalone.py`** - Standalone test script

## Quick Start

### Installation

The parser requires `lxml`, which is already in your `requirements.txt`:

```bash
pip install lxml>=5.0.0
```

### Basic Usage

```python
from app.services.scrapers.xml_parser import GermanLegalXMLParser

# Initialize parser
parser = GermanLegalXMLParser()

# Parse from file
dokumente = parser.parse_file('path/to/legal_document.xml')

# Or parse from string
xml_content = """<?xml version="1.0"?>..."""
dokumente = parser.parse_string(xml_content)

# Access data
for norm in dokumente.norms:
    print(f"Law: {norm.metadaten.jurabk}")
    print(f"Section: {norm.metadaten.enbez}")
    print(f"Title: {norm.metadaten.titel}")

    if norm.textdaten and norm.textdaten.text:
        print(f"Content: {norm.textdaten.text.formatted_text.content}")
```

## Data Structure

### Main Classes

The parser creates structured dataclasses for all DTD elements:

```python
@dataclass
class Dokumente:
    """Root container"""
    norms: List[Norm]
    builddate: Optional[str]
    doknr: Optional[str]

@dataclass
class Norm:
    """A single legal norm"""
    metadaten: Metadaten
    textdaten: Optional[Textdaten]
    builddate: Optional[str]
    doknr: Optional[str]

@dataclass
class Metadaten:
    """Metadata section"""
    jurabk: List[str]                    # Legal abbreviation(s)
    amtabk: Optional[str]                # Official abbreviation
    ausfertigung_datum: Optional[str]    # Promulgation date
    fundstelle: List[Fundstelle]         # Citations
    kurzue: Optional[str]                # Short title
    langue: Optional[str]                # Long title
    gliederungseinheit: Optional[Gliederungseinheit]  # Structure
    enbez: Optional[str]                 # Section designation (e.g., "§ 1")
    titel: Optional[str]                 # Title
    standangabe: List[Standangabe]       # Version info

@dataclass
class Textdaten:
    """Text content section"""
    text: Optional[TextContent]
    fussnoten: Optional[TextContent]

@dataclass
class FormattedText:
    """Formatted text with structure"""
    content: str                         # Full text content
    paragraphs: List[str]                # Individual paragraphs
    tables: List[Table]                  # Tables
    footnote_refs: List[str]             # Footnote references
```

## Features

### 1. Complete DTD Coverage

The parser handles all major elements from the gii-norm.dtd:

- ✅ Document-level metadata (`builddate`, `doknr`)
- ✅ Legal abbreviations (`jurabk`, `amtabk`)
- ✅ Dates (`ausfertigung-datum`)
- ✅ Citations (`fundstelle` with `periodikum`, `zitstelle`)
- ✅ Titles (`kurzue`, `langue`, `titel`)
- ✅ Structural classification (`gliederungseinheit`)
- ✅ Section designations (`enbez`)
- ✅ Version information (`standangabe`)
- ✅ Text content with formatting
- ✅ Tables (preserved as raw XML for custom processing)
- ✅ Footnotes with references

### 2. Text Extraction

The parser intelligently extracts text while preserving structure:

```python
# Handles formatting elements
<P>Text with <B>bold</B> and <I>italic</I></P>
# Result: "Text with bold and italic"

# Preserves line breaks
<P>Line 1<BR/>Line 2<BR/>Line 3</P>
# Result: "Line 1\nLine 2\nLine 3"

# Extracts nested content
<Content>
    <P>Paragraph 1</P>
    <P>Paragraph 2</P>
</Content>
# Results in paragraphs list: ["Paragraph 1", "Paragraph 2"]
```

### 3. Metadata Parsing

Complete metadata extraction:

```python
norm = dokumente.norms[0]
m = norm.metadaten

# Basic identification
print(m.jurabk)           # ["BGB"]
print(m.enbez)            # "§ 1"
print(m.titel)            # "Beginn der Rechtsfähigkeit"

# Citations
for fundstelle in m.fundstelle:
    print(f"{fundstelle.periodikum} {fundstelle.zitstelle}")
    # "BGBl I 1896, 195"

# Structural information
if m.gliederungseinheit:
    print(m.gliederungseinheit.gliederungskennzahl)  # "400-2"
    print(m.gliederungseinheit.gliederungsbez)       # "Buch 1"
    print(m.gliederungseinheit.gliederungstitel)     # "Allgemeiner Teil"

# Version info
for stand in m.standangabe:
    print(f"{stand.standtyp}: {stand.standkommentar}")
```

### 4. Multiple Norms

The parser handles documents with multiple norms:

```python
dokumente = parser.parse_file('bgb_multiple_sections.xml')

for norm in dokumente.norms:
    print(f"{norm.metadaten.enbez}: {norm.metadaten.titel}")
# Output:
# § 1: Beginn der Rechtsfähigkeit
# § 2: Eintritt der Volljährigkeit
# § 3: Handlungsfähigkeit
```

### 5. Dictionary/JSON Export

Convert parsed data to dictionaries for JSON serialization:

```python
norm_dict = parser.to_dict(norm)

import json
json_output = json.dumps(norm_dict, indent=2, ensure_ascii=False)

# Save to file
with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(norm_dict, f, indent=2, ensure_ascii=False)
```

## Integration with Scraper

Integrate the parser with the `GesetzImInternetScraper`:

```python
from app.services.scrapers.gesetzte_im_internet_scraper import GesetzImInternetScraper
from app.services.scrapers.xml_parser import GermanLegalXMLParser

# Scrape XML from website
scraper = GesetzImInternetScraper()
xml_content = scraper.fetch_law_xml('bgb')

# Parse the XML
parser = GermanLegalXMLParser()
dokumente = parser.parse_string(xml_content)

# Process parsed data
for norm in dokumente.norms:
    # Store in database
    legal_text = LegalText(
        title=norm.metadaten.titel,
        content=norm.textdaten.text.formatted_text.content if norm.textdaten else "",
        source_url=f"https://www.gesetze-im-internet.de/bgb/{norm.metadaten.enbez}",
        metadata={
            "jurabk": norm.metadaten.jurabk,
            "enbez": norm.metadaten.enbez,
            "ausfertigung_datum": norm.metadaten.ausfertigung_datum,
        }
    )
    # Save to database...
```

## Example XML

The parser handles XML like this:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<dokumente builddate="2024-01-15" doknr="BJNR001950896">
    <norm builddate="2024-01-15" doknr="BJNR001950896BJNE000100314">
        <metadaten>
            <jurabk>BGB</jurabk>
            <amtabk>BGB</amtabk>
            <ausfertigung-datum manuell="ja">1896-08-18</ausfertigung-datum>
            <fundstelle typ="amtlich">
                <periodikum>BGBl I</periodikum>
                <zitstelle>1896, 195</zitstelle>
            </fundstelle>
            <kurzue>Bürgerliches Gesetzbuch</kurzue>
            <langue>Bürgerliches Gesetzbuch in der Fassung...</langue>
            <gliederungseinheit>
                <gliederungskennzahl>400-2</gliederungskennzahl>
                <gliederungsbez>Buch 1</gliederungsbez>
                <gliederungstitel>Allgemeiner Teil</gliederungstitel>
            </gliederungseinheit>
            <enbez>§ 1</enbez>
            <titel format="parat">Beginn der Rechtsfähigkeit</titel>
            <standangabe checked="ja">
                <standtyp>Stand</standtyp>
                <standkommentar>Zuletzt geändert durch Art. 10 G v. 30.3.2021 I 607</standkommentar>
            </standangabe>
        </metadaten>
        <textdaten>
            <text format="XML">
                <Content>
                    <P>Die Rechtsfähigkeit des Menschen beginnt mit der Vollendung der Geburt.</P>
                </Content>
            </text>
        </textdaten>
    </norm>
</dokumente>
```

## Testing

Run the test suite:

```bash
# With pytest installed
pytest tests/test_xml_parser.py -v

# Or use the standalone test
python3 test_parser_standalone.py
```

The test suite includes 15 tests covering:

- Parser initialization
- Simple XML parsing
- Metadata extraction
- Text content parsing
- Complex metadata with all elements
- Multiple paragraphs
- Dictionary conversion
- Line break handling
- Empty documents
- Multiple jurabk elements

## Advanced Usage

### Custom Table Processing

Tables are preserved as raw XML for custom processing:

```python
for table in formatted_text.tables:
    if table.title:
        print(f"Table: {table.title}")

    # Process raw XML
    table_xml = table.raw_content
    # Custom table rendering logic here...
```

### Footnote Handling

Access footnotes and their references:

```python
text_content = norm.textdaten.text

# Get footnote references in text
for ref_id in text_content.formatted_text.footnote_refs:
    print(f"Footnote reference: {ref_id}")

# Get actual footnotes
for footnote in text_content.footnotes:
    print(f"[{footnote.id}] {footnote.content}")
```

### Batch Processing

Process multiple files:

```python
from pathlib import Path

parser = GermanLegalXMLParser()
xml_dir = Path('legal_texts')

for xml_file in xml_dir.glob('*.xml'):
    try:
        dokumente = parser.parse_file(str(xml_file))
        print(f"Processed {xml_file.name}: {len(dokumente.norms)} norms")

        # Store in database, index, etc.
        for norm in dokumente.norms:
            process_norm(norm)

    except Exception as e:
        print(f"Error processing {xml_file.name}: {e}")
```

## Performance Considerations

- The parser uses `lxml` for fast XML processing
- Memory efficient: processes documents incrementally
- Suitable for large documents with many norms
- Dictionary conversion adds minimal overhead

## Limitations

1. **Tables**: Stored as raw XML. You'll need additional processing to render them in your desired format (HTML, Markdown, etc.)

2. **Images**: `IMG` and `FILE` elements are not fully processed. The file paths are preserved but images are not downloaded.

3. **Complex Formatting**: Some advanced formatting (fonts, sizes, special characters) are partially preserved but may need custom handling.

4. **DTD Validation**: The parser doesn't validate against the DTD. It assumes well-formed XML.

## Type Safety

The parser uses Python type hints throughout:

- All methods have proper type annotations
- Dataclasses provide runtime type checking
- Compatible with `mypy` and other type checkers
- Only 2 minor type inference warnings (non-critical)

## Documentation Files

1. **`README_PARSER.md`** - Complete API reference with detailed examples
2. **`PARSER_USAGE.md`** - This file (usage guide and quick reference)
3. **Inline docstrings** - All classes and methods are documented

## Next Steps

To start using the parser:

1. **Install dependencies** (if not already installed):

   ```bash
   pip install -r requirements.txt
   ```

2. **Run the example**:

   ```bash
   python3 examples/parse_example.py
   ```

3. **Run tests**:

   ```bash
   pytest tests/test_xml_parser.py -v
   ```

4. **Integrate with your application**:
   - Import `GermanLegalXMLParser`
   - Parse XML from files or strings
   - Process the structured data
   - Store in your database or index

## Support

For detailed API documentation, see `README_PARSER.md`.

For examples, see:

- `examples/parse_example.py` - Comprehensive example
- `tests/test_xml_parser.py` - Test examples
- `xml_parser.py` (bottom) - Basic usage in `__main__`

## Version Information

**Parser Version**: 1.0
**DTD Version**: gii-norm.dtd v1.01 (2012-06-25)
**Python**: 3.7+
