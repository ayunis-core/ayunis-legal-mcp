"""
Parser for German legal text XML format (gii-norm.dtd)

This module provides a comprehensive parser for XML documents following the
gii-norm.dtd structure used by gesetze-im-internet.de.

The parser uses lxml for XML processing and dataclasses for structured data representation.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from lxml import etree
from io import StringIO, BytesIO


@dataclass
class Fundstelle:
    """Represents a legal citation source (fundstelle)"""

    periodikum: str
    zitstelle: str
    typ: Optional[str] = None  # 'amtlich' or 'nichtamtlich'
    anlagedat: Optional[str] = None
    dokst: Optional[str] = None
    abgabedat: Optional[str] = None


@dataclass
class Gliederungseinheit:
    """Represents a structural unit (gliederungseinheit)"""

    gliederungskennzahl: str
    gliederungsbez: Optional[str] = None
    gliederungstitel: Optional[str] = None


@dataclass
class Standangabe:
    """Represents version information (standangabe)"""

    standtyp: str
    standkommentar: str
    checked: Optional[str] = None


@dataclass
class Metadaten:
    """Represents metadata for a legal norm"""

    jurabk: List[str]  # Legal abbreviation(s)
    amtabk: Optional[str] = None  # Official abbreviation
    ausfertigung_datum: Optional[str] = None  # Promulgation date
    ausfertigung_datum_manuell: Optional[str] = None
    fundstelle: List[Fundstelle] = field(default_factory=list)
    kurzue: Optional[str] = None  # Short title
    langue: Optional[str] = None  # Long title
    gliederungseinheit: Optional[Gliederungseinheit] = None
    enbez: Optional[str] = None  # Designation
    titel: Optional[str] = None  # Title
    titel_format: Optional[str] = None
    standangabe: List[Standangabe] = field(default_factory=list)


@dataclass
class Table:
    """Represents a table structure"""

    title: Optional[str] = None
    html_representation: Optional[str] = None
    raw_content: Optional[str] = None


@dataclass
class FormattedText:
    """Represents formatted text with structure preserved"""

    content: str
    paragraphs: List[str] = field(default_factory=list)
    tables: List[Table] = field(default_factory=list)
    footnote_refs: List[str] = field(default_factory=list)


@dataclass
class Footnote:
    """Represents a footnote"""

    id: str
    content: str
    prefix: Optional[str] = None
    fnz: Optional[str] = None
    postfix: Optional[str] = None
    pos: Optional[str] = None
    group: Optional[str] = None


@dataclass
class TextContent:
    """Represents the text content section"""

    formatted_text: Optional[FormattedText] = None
    footnotes: List[Footnote] = field(default_factory=list)
    format: Optional[str] = None


@dataclass
class Textdaten:
    """Represents text data for a legal norm"""

    text: Optional[TextContent] = None
    fussnoten: Optional[TextContent] = None  # Additional footnotes section


@dataclass
class Norm:
    """Represents a complete legal norm"""

    metadaten: Metadaten
    textdaten: Optional[Textdaten] = None
    builddate: Optional[str] = None
    doknr: Optional[str] = None


@dataclass
class Dokumente:
    """Root element containing multiple norms"""

    norms: List[Norm] = field(default_factory=list)
    builddate: Optional[str] = None
    doknr: Optional[str] = None


class GermanLegalXMLParser:
    """Parser for German legal XML documents (gii-norm.dtd format)"""

    def __init__(self):
        self.namespaces = {}

    def parse_bytes(self, xml_bytes: bytes) -> Dokumente:
        """
        Parse an XML bytes containing German legal texts
        """
        tree = etree.parse(BytesIO(xml_bytes))
        root = tree.getroot()
        return self.parse_dokumente(root)

    def parse_file(self, filepath: str) -> Dokumente:
        """
        Parse an XML file containing German legal texts

        Args:
            filepath: Path to the XML file

        Returns:
            Dokumente object containing parsed norms
        """
        tree = etree.parse(filepath)
        root = tree.getroot()
        return self.parse_dokumente(root)

    def parse_string(self, xml_string: str) -> Dokumente:
        """
        Parse an XML string containing German legal texts

        Args:
            xml_string: XML content as string

        Returns:
            Dokumente object containing parsed norms
        """
        tree = etree.parse(StringIO(xml_string))
        root = tree.getroot()
        return self.parse_dokumente(root)

    def parse_dokumente(self, element: Any) -> Dokumente:
        """Parse the root dokumente element"""
        dokumente = Dokumente(
            builddate=element.get("builddate"), doknr=element.get("doknr")
        )

        for norm_elem in element.findall("norm"):
            norm = self.parse_norm(norm_elem)
            dokumente.norms.append(norm)

        return dokumente

    def parse_norm(self, element: Any) -> Norm:
        """Parse a norm element"""
        metadaten_elem = element.find("metadaten")
        textdaten_elem = element.find("textdaten")

        metadaten = (
            self.parse_metadaten(metadaten_elem)
            if metadaten_elem is not None
            else Metadaten(jurabk=[])
        )
        textdaten = (
            self.parse_textdaten(textdaten_elem) if textdaten_elem is not None else None
        )

        return Norm(
            metadaten=metadaten,
            textdaten=textdaten,
            builddate=element.get("builddate"),
            doknr=element.get("doknr"),
        )

    def parse_metadaten(self, element: Any) -> Metadaten:
        """Parse metadata section"""
        metadaten = Metadaten(jurabk=[])

        # Parse jurabk (can have multiple)
        for jurabk_elem in element.findall("jurabk"):
            if jurabk_elem.text:
                metadaten.jurabk.append(jurabk_elem.text.strip())

        # Parse amtabk
        amtabk_elem = element.find("amtabk")
        if amtabk_elem is not None and amtabk_elem.text:
            metadaten.amtabk = amtabk_elem.text.strip()

        # Parse ausfertigung-datum
        datum_elem = element.find("ausfertigung-datum")
        if datum_elem is not None:
            if datum_elem.text:
                metadaten.ausfertigung_datum = datum_elem.text.strip()
            metadaten.ausfertigung_datum_manuell = datum_elem.get("manuell")

        # Parse fundstelle (can have multiple)
        for fundstelle_elem in element.findall("fundstelle"):
            fundstelle = self.parse_fundstelle(fundstelle_elem)
            if fundstelle:
                metadaten.fundstelle.append(fundstelle)

        # Parse kurzue
        kurzue_elem = element.find("kurzue")
        if kurzue_elem is not None:
            metadaten.kurzue = self.extract_text_content(kurzue_elem)

        # Parse langue
        langue_elem = element.find("langue")
        if langue_elem is not None:
            metadaten.langue = self.extract_text_content(langue_elem)

        # Parse gliederungseinheit
        gliederung_elem = element.find("gliederungseinheit")
        if gliederung_elem is not None:
            metadaten.gliederungseinheit = self.parse_gliederungseinheit(
                gliederung_elem
            )

        # Parse enbez
        enbez_elem = element.find("enbez")
        if enbez_elem is not None and enbez_elem.text:
            metadaten.enbez = enbez_elem.text.strip()

        # Parse titel
        titel_elem = element.find("titel")
        if titel_elem is not None:
            metadaten.titel = self.extract_text_content(titel_elem)
            metadaten.titel_format = titel_elem.get("format")

        # Parse standangabe (can have multiple)
        for stand_elem in element.findall("standangabe"):
            standangabe = self.parse_standangabe(stand_elem)
            if standangabe:
                metadaten.standangabe.append(standangabe)

        return metadaten

    def parse_fundstelle(self, element: Any) -> Optional[Fundstelle]:
        """Parse a fundstelle (citation source) element"""
        periodikum_elem = element.find("periodikum")
        zitstelle_elem = element.find("zitstelle")

        if periodikum_elem is None or zitstelle_elem is None:
            return None

        fundstelle = Fundstelle(
            periodikum=periodikum_elem.text.strip() if periodikum_elem.text else "",
            zitstelle=zitstelle_elem.text.strip() if zitstelle_elem.text else "",
            typ=element.get("typ"),
        )

        # Parse anlageabgabe if present
        anlageabgabe_elem = element.find("anlageabgabe")
        if anlageabgabe_elem is not None:
            anlagedat_elem = anlageabgabe_elem.find("anlagedat")
            dokst_elem = anlageabgabe_elem.find("dokst")
            abgabedat_elem = anlageabgabe_elem.find("abgabedat")

            if anlagedat_elem is not None and anlagedat_elem.text:
                fundstelle.anlagedat = anlagedat_elem.text.strip()
            if dokst_elem is not None and dokst_elem.text:
                fundstelle.dokst = dokst_elem.text.strip()
            if abgabedat_elem is not None and abgabedat_elem.text:
                fundstelle.abgabedat = abgabedat_elem.text.strip()

        return fundstelle

    def parse_gliederungseinheit(self, element: Any) -> Optional[Gliederungseinheit]:
        """Parse a gliederungseinheit (structural unit) element"""
        kennzahl_elem = element.find("gliederungskennzahl")

        if kennzahl_elem is None or not kennzahl_elem.text:
            return None

        gliederung = Gliederungseinheit(gliederungskennzahl=kennzahl_elem.text.strip())

        bez_elem = element.find("gliederungsbez")
        if bez_elem is not None and bez_elem.text:
            gliederung.gliederungsbez = bez_elem.text.strip()

        titel_elem = element.find("gliederungstitel")
        if titel_elem is not None:
            gliederung.gliederungstitel = self.extract_text_content(titel_elem)

        return gliederung

    def parse_standangabe(self, element: Any) -> Optional[Standangabe]:
        """Parse a standangabe (version information) element"""
        standtyp_elem = element.find("standtyp")
        standkommentar_elem = element.find("standkommentar")

        if standtyp_elem is None or standkommentar_elem is None:
            return None

        return Standangabe(
            standtyp=standtyp_elem.text.strip() if standtyp_elem.text else "",
            standkommentar=self.extract_text_content(standkommentar_elem),
            checked=element.get("checked"),
        )

    def parse_textdaten(self, element: Any) -> Textdaten:
        """Parse the textdaten section"""
        textdaten = Textdaten()

        text_elem = element.find("text")
        if text_elem is not None:
            textdaten.text = self.parse_text_content(text_elem)

        fussnoten_elem = element.find("fussnoten")
        if fussnoten_elem is not None:
            textdaten.fussnoten = self.parse_text_content(fussnoten_elem)

        return textdaten

    def parse_text_content(self, element: Any) -> TextContent:
        """Parse a text or fussnoten element"""
        text_content = TextContent(format=element.get("format"))

        # Parse TOC or Content
        content_elem = element.find("Content")
        toc_elem = element.find("TOC")

        target_elem = content_elem if content_elem is not None else toc_elem
        if target_elem is not None:
            text_content.formatted_text = self.parse_formatted_content(target_elem)

        # Parse Footnotes
        footnotes_elem = element.find("Footnotes")
        if footnotes_elem is not None:
            for footnote_elem in footnotes_elem.findall("Footnote"):
                footnote = self.parse_footnote(footnote_elem)
                if footnote:
                    text_content.footnotes.append(footnote)

        return text_content

    def parse_formatted_content(self, element: Any) -> FormattedText:
        """Parse formatted content (Content or TOC element)"""
        formatted_text = FormattedText(content="")

        # Extract paragraphs
        for p_elem in element.findall(".//P"):
            paragraph_text = self.extract_text_content(p_elem)
            if paragraph_text:
                formatted_text.paragraphs.append(paragraph_text)

        # Extract tables
        for table_elem in element.findall(".//table"):
            table = self.parse_table(table_elem)
            formatted_text.tables.append(table)

        # Extract all text content
        formatted_text.content = self.extract_text_content(element)

        # Extract footnote references
        for fnr_elem in element.findall(".//FnR"):
            fn_id = fnr_elem.get("ID")
            if fn_id:
                formatted_text.footnote_refs.append(fn_id)

        return formatted_text

    def parse_table(self, element: Any) -> Table:
        """Parse a table element"""
        table = Table()

        # Extract title if present
        title_elem = element.find("Title")
        if title_elem is not None:
            table.title = self.extract_text_content(title_elem)

        # Store raw content for later processing
        table.raw_content = etree.tostring(element, encoding="unicode", method="xml")

        return table

    def parse_footnote(self, element: Any) -> Optional[Footnote]:
        """Parse a Footnote element"""
        footnote_id = element.get("ID")
        if not footnote_id:
            return None

        return Footnote(
            id=footnote_id,
            content=self.extract_text_content(element),
            prefix=element.get("Prefix"),
            fnz=element.get("FnZ"),
            postfix=element.get("Postfix"),
            pos=element.get("Pos"),
            group=element.get("Group"),
        )

    def extract_text_content(self, element: Any) -> str:
        """
        Extract text content from an element, handling formatting tags

        This recursively extracts text from the element and its children,
        handling line breaks and basic formatting.
        """

        def extract_recursive(elem: Any) -> str:
            text_parts: List[str] = []

            # Add element's direct text
            if elem.text:
                text_parts.append(str(elem.text))

            # Process children
            for child in elem:
                # Handle line breaks
                if child.tag == "BR":
                    text_parts.append("\n")
                else:
                    # Recursively extract from child
                    child_text = extract_recursive(child)
                    if child_text:
                        text_parts.append(child_text)

                # Add tail text (text after the closing tag)
                if child.tail:
                    text_parts.append(str(child.tail))

            return "".join(text_parts)

        text = extract_recursive(element)
        # Clean up excessive whitespace while preserving line breaks
        lines = [line.strip() for line in text.split("\n")]
        return "\n".join(line for line in lines if line)

    def to_dict(self, obj: Any) -> Dict[str, Any]:
        """
        Convert parsed objects to dictionary representation

        Useful for JSON serialization or further processing
        """
        if hasattr(obj, "__dataclass_fields__"):
            result: Dict[str, Any] = {}
            for field_name in obj.__dataclass_fields__:
                value: Any = getattr(obj, field_name)
                if isinstance(value, list):
                    converted_list: List[Any] = []
                    item: Any
                    for item in value:  # type: ignore
                        if hasattr(item, "__dataclass_fields__"):  # type: ignore
                            converted_list.append(self.to_dict(item))
                        else:
                            converted_list.append(item)
                    result[field_name] = converted_list
                elif hasattr(value, "__dataclass_fields__"):
                    result[field_name] = self.to_dict(value)
                else:
                    result[field_name] = value
            return result
        return {"value": obj}


# Example usage
if __name__ == "__main__":
    parser = GermanLegalXMLParser()

    # Example: Parse a file
    # dokumente = parser.parse_file('path/to/legal_text.xml')

    # Example: Parse a string
    xml_example = """<?xml version="1.0" encoding="UTF-8"?>
    <dokumente builddate="2024-01-01">
        <norm doknr="123">
            <metadaten>
                <jurabk>BGB</jurabk>
                <amtabk>BGB</amtabk>
                <ausfertigung-datum manuell="ja">1896-08-18</ausfertigung-datum>
                <langue>Bürgerliches Gesetzbuch</langue>
                <enbez>§ 1</enbez>
                <titel>Beginn der Rechtsfähigkeit</titel>
            </metadaten>
            <textdaten>
                <text>
                    <Content>
                        <P>Die Rechtsfähigkeit des Menschen beginnt mit der Vollendung der Geburt.</P>
                    </Content>
                </text>
            </textdaten>
        </norm>
    </dokumente>
    """

    # dokumente = parser.parse_string(xml_example)
    # print(f"Parsed {len(dokumente.norms)} norm(s)")
    #
    # if dokumente.norms:
    #     norm = dokumente.norms[0]
    #     print(f"Jurabk: {norm.metadaten.jurabk}")
    #     print(f"Title: {norm.metadaten.titel}")
    #     if norm.textdaten and norm.textdaten.text and norm.textdaten.text.formatted_text:
    #         print(f"Content: {norm.textdaten.text.formatted_text.content}")
