# German Legal XML Parser

This parser handles XML documents following the **gii-norm.dtd** format used by [gesetze-im-internet.de](https://www.gesetze-im-internet.de) for publishing German federal laws and regulations.

## Features

- **Complete DTD Coverage**: Parses all major elements defined in the gii-norm.dtd
- **Structured Data**: Uses dataclasses for type-safe representation
- **Text Extraction**: Handles complex nested text with formatting elements
- **Table Support**: Captures table structures
- **Footnote Handling**: Extracts footnotes with references
- **Metadata Parsing**: Complete metadata extraction including dates, citations, and structural information

## Installation

The parser requires `lxml`:

```bash
pip install lxml
```

## Usage

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

# Access parsed data
for norm in dokumente.norms:
    print(f"Law: {norm.metadaten.jurabk}")
    print(f"Section: {norm.metadaten.enbez}")
    print(f"Title: {norm.metadaten.titel}")

    if norm.textdaten and norm.textdaten.text:
        if norm.textdaten.text.formatted_text:
            print(f"Content: {norm.textdaten.text.formatted_text.content}")
```

### Accessing Metadata

```python
norm = dokumente.norms[0]
metadata = norm.metadaten

# Legal abbreviations
print(f"Jurabk: {metadata.jurabk}")  # List of abbreviations

# Dates
print(f"Promulgation date: {metadata.ausfertigung_datum}")

# Titles
print(f"Short title: {metadata.kurzue}")
print(f"Long title: {metadata.langue}")

# Citations
for fundstelle in metadata.fundstelle:
    print(f"Published in: {fundstelle.periodikum} {fundstelle.zitstelle}")
    print(f"Type: {fundstelle.typ}")

# Version information
for stand in metadata.standangabe:
    print(f"Version type: {stand.standtyp}")
    print(f"Comment: {stand.standkommentar}")
```

### Accessing Text Content

```python
if norm.textdaten and norm.textdaten.text:
    text_content = norm.textdaten.text

    # Get formatted text
    if text_content.formatted_text:
        fmt = text_content.formatted_text

        # Full text content
        print(fmt.content)

        # Individual paragraphs
        for para in fmt.paragraphs:
            print(f"Paragraph: {para}")

        # Tables
        for table in fmt.tables:
            print(f"Table title: {table.title}")
            print(f"Table XML: {table.raw_content}")

        # Footnote references
        print(f"Footnote refs: {fmt.footnote_refs}")

    # Access footnotes
    for footnote in text_content.footnotes:
        print(f"Footnote {footnote.id}: {footnote.content}")
```

### Structural Information

```python
# Access structural unit information
if metadata.gliederungseinheit:
    glie = metadata.gliederungseinheit
    print(f"Classification code: {glie.gliederungskennzahl}")
    print(f"Classification designation: {glie.gliederungsbez}")
    print(f"Classification title: {glie.gliederungstitel}")
```

### Convert to Dictionary

```python
# Convert parsed data to dictionary (useful for JSON serialization)
norm_dict = parser.to_dict(norm)
print(norm_dict)

# You can then serialize to JSON
import json
json_output = json.dumps(norm_dict, indent=2, ensure_ascii=False)
```

## Data Structure

### Main Classes

- **`Dokumente`**: Root container for multiple norms
- **`Norm`**: Single legal norm with metadata and text
- **`Metadaten`**: Metadata including titles, dates, citations
- **`Textdaten`**: Text content and footnotes
- **`FormattedText`**: Structured text with paragraphs and tables
- **`Footnote`**: Individual footnote with content

### Key Metadata Fields

| Field                | Description                                 |
| -------------------- | ------------------------------------------- |
| `jurabk`             | Legal abbreviation (e.g., "BGB", "StGB")    |
| `amtabk`             | Official abbreviation                       |
| `ausfertigung_datum` | Promulgation date                           |
| `fundstelle`         | Citation sources (where published)          |
| `kurzue`             | Short title                                 |
| `langue`             | Long title                                  |
| `enbez`              | Section designation (e.g., "§ 1", "Art. 1") |
| `titel`              | Title of the section                        |
| `gliederungseinheit` | Structural classification                   |
| `standangabe`        | Version/status information                  |

## Advanced Features

### Handling Complex Formatting

The parser preserves text structure while extracting content:

- **Line breaks** (BR elements) are converted to `\n`
- **Bold, Italic, Underline** (B, I, U) are preserved in content
- **Superscript/Subscript** (SUP, SUB) text is included
- **Tables** are captured with structure preserved
- **Citations** are maintained in text flow

### Text Extraction

The `extract_text_content()` method recursively processes:

- Direct text content
- Nested formatting elements
- Special elements like BR, Citation, etc.
- Tail text after elements

### Table Parsing

Tables are complex structures. The parser:

- Extracts table titles
- Preserves the raw XML representation
- Allows for custom table processing if needed

## Examples

### Complete Example

```python
from app.services.scrapers.xml_parser import GermanLegalXMLParser
import json

parser = GermanLegalXMLParser()

# Parse a legal document
dokumente = parser.parse_file('bgb_section.xml')

print(f"Document build date: {dokumente.builddate}")
print(f"Number of norms: {len(dokumente.norms)}")

for i, norm in enumerate(dokumente.norms):
    print(f"\n=== Norm {i+1} ===")

    m = norm.metadaten
    print(f"Law: {', '.join(m.jurabk)}")
    print(f"Section: {m.enbez}")
    print(f"Title: {m.titel}")

    if m.ausfertigung_datum:
        print(f"Date: {m.ausfertigung_datum}")

    if m.fundstelle:
        print("Citations:")
        for f in m.fundstelle:
            print(f"  - {f.periodikum} {f.zitstelle}")

    if norm.textdaten and norm.textdaten.text:
        txt = norm.textdaten.text.formatted_text
        if txt:
            print(f"\nContent:")
            print(txt.content[:200] + "..." if len(txt.content) > 200 else txt.content)

            if txt.footnote_refs:
                print(f"\nFootnotes: {', '.join(txt.footnote_refs)}")

# Export to JSON
output = {
    'builddate': dokumente.builddate,
    'norms': [parser.to_dict(norm) for norm in dokumente.norms]
}

with open('parsed_output.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)
```

### Processing Multiple Files

```python
import os
from pathlib import Path

parser = GermanLegalXMLParser()
all_norms = []

# Process all XML files in a directory
xml_dir = Path('legal_texts')
for xml_file in xml_dir.glob('*.xml'):
    try:
        dokumente = parser.parse_file(str(xml_file))
        all_norms.extend(dokumente.norms)
        print(f"Processed {xml_file.name}: {len(dokumente.norms)} norms")
    except Exception as e:
        print(f"Error processing {xml_file.name}: {e}")

print(f"\nTotal norms processed: {len(all_norms)}")
```

## DTD Reference

The parser is based on **gii-norm.dtd** version 1.01 (dated 25.06.2012) from juris GmbH.

### Main Elements

- `dokumente`: Root element containing multiple norms
- `norm`: Individual legal norm
- `metadaten`: Metadata section
- `textdaten`: Text content section
- `text`: Main text with optional TOC/Content
- `fussnoten`: Additional footnotes section

### Formatting Elements

- `BR`: Line break
- `B`, `I`, `U`: Bold, italic, underline
- `SUP`, `SUB`: Superscript, subscript
- `Citation`: Legal citation
- `table`: Table structure with tgroup, thead, tbody
- `P`: Paragraph
- `DL`, `DT`, `DD`: Definition list
- `FnR`: Footnote reference
- `Footnote`: Footnote definition

## Limitations

1. **Table Rendering**: Tables are stored as raw XML. You may need additional processing to render them in your desired format.
2. **Complex Formatting**: Some advanced formatting (fonts, sizes, etc.) are partially preserved in the text but may need custom handling.
3. **Images**: IMG and FILE elements are not fully processed (paths are preserved).

## Integration with Legal MCP Server

This parser can be integrated with the existing scraper:

```python
from app.services.scrapers.xml_parser import GermanLegalXMLParser
from app.services.scrapers.gesetzte_im_internet_scraper import GesetzImInternetScraper

# Scrape XML content
scraper = GesetzImInternetScraper()
xml_content = scraper.fetch_law_xml('bgb')

# Parse the XML
parser = GermanLegalXMLParser()
dokumente = parser.parse_string(xml_content)

# Store in database or process further
for norm in dokumente.norms:
    # Save to database, index, etc.
    pass
```

## License

This parser is designed for use with publicly available German legal texts from gesetze-im-internet.de.
