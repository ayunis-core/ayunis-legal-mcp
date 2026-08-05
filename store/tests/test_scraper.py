"""
Tests for GesetzteImInternetScraper

These tests validate:
1. Sub-section extraction from paragraph text
2. Paragraph grouping and concatenation by sub-section
3. Unique (code, section, sub_section) tuples in output
4. ZIP extraction functionality
5. XML parsing integration
6. Error handling for network and parsing failures
7. Edge cases in legal text structure
"""

import pytest
import zipfile
import io
from unittest.mock import patch, MagicMock
from requests.exceptions import HTTPError, ConnectionError, Timeout
from app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper import (
    GesetzteImInternetScraper,
)
from app.scrapers.gesetze_im_internet.xml_parser import (
    Dokumente,
    Norm,
    Metadaten,
    Textdaten,
    TextContent,
    FormattedText,
)


class TestExtractSubSection:
    """Tests for _extract_sub_section method"""

    def setup_method(self):
        self.scraper = GesetzteImInternetScraper()

    def test_extracts_single_digit_subsection(self):
        """Should extract '1' from '(1) Some text'"""
        result = self.scraper._extract_sub_section("(1) Die Rechtsfähigkeit...")
        assert result == "1"

    def test_extracts_double_digit_subsection(self):
        """Should extract '12' from '(12) Some text'"""
        result = self.scraper._extract_sub_section("(12) Some longer text here")
        assert result == "12"

    def test_extracts_alphanumeric_subsection(self):
        """Should extract '2a' from '(2a) Some text'"""
        result = self.scraper._extract_sub_section("(2a) Mixed numbering")
        assert result == "2a"

    def test_returns_empty_for_no_subsection(self):
        """Should return empty string when no (n) pattern"""
        result = self.scraper._extract_sub_section("Regular paragraph text")
        assert result == ""

    def test_returns_empty_for_parenthesis_mid_text(self):
        """Should return empty when parenthesis is not at start"""
        result = self.scraper._extract_sub_section("Text with (1) in middle")
        assert result == ""


class TestScrapeDeduplication:
    """Tests for scrape method's paragraph grouping logic"""

    def setup_method(self):
        self.scraper = GesetzteImInternetScraper()

    def _create_mock_dokumente(self, norms_data: list) -> Dokumente:
        """Helper to create Dokumente with specified norms"""
        norms = []
        for norm_data in norms_data:
            formatted_text = FormattedText(
                content="",
                paragraphs=norm_data["paragraphs"],
            )
            text_content = TextContent(formatted_text=formatted_text)
            textdaten = Textdaten(text=text_content)
            metadaten = Metadaten(
                jurabk=[norm_data.get("jurabk", "BGB")],
                enbez=norm_data.get("enbez"),
            )
            norms.append(Norm(metadaten=metadaten, textdaten=textdaten))
        return Dokumente(norms=norms)

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_concatenates_paragraphs_with_same_subsection(
        self, mock_requests, mock_extract_xml
    ):
        """Paragraphs without (n) pattern should be concatenated"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        # Two paragraphs without sub-section markers -> should be concatenated
        dokumente = self._create_mock_dokumente([
            {
                "enbez": "§ 1",
                "paragraphs": [
                    "First paragraph without number.",
                    "Second paragraph without number.",
                ],
            }
        ])

        with patch.object(
            GesetzteImInternetScraper, "scrape"
        ) as mock_scrape:
            # Bypass network call, test the logic directly
            pass

        # Test the actual logic by calling a modified approach
        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        assert len(result) == 1
        assert result[0].sub_section == ""
        assert "First paragraph" in result[0].text
        assert "Second paragraph" in result[0].text
        assert "\n\n" in result[0].text

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_separates_numbered_subsections(self, mock_requests, mock_extract_xml):
        """Paragraphs with different (n) patterns should be separate entries"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        dokumente = self._create_mock_dokumente([
            {
                "enbez": "§ 1",
                "paragraphs": [
                    "(1) First subsection text.",
                    "(2) Second subsection text.",
                    "(3) Third subsection text.",
                ],
            }
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        assert len(result) == 3
        sub_sections = {r.sub_section for r in result}
        assert sub_sections == {"1", "2", "3"}

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_mixed_numbered_and_unnumbered_paragraphs(
        self, mock_requests, mock_extract_xml
    ):
        """Mix of numbered and unnumbered paragraphs handled correctly"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        dokumente = self._create_mock_dokumente([
            {
                "enbez": "§ 1",
                "paragraphs": [
                    "(1) First numbered.",
                    "Continuation of first.",  # Should join with empty sub_section
                    "(2) Second numbered.",
                    "Another unnumbered.",  # Should join with previous unnumbered
                ],
            }
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        # Should have 3 entries: sub_section "1", "2", and ""
        assert len(result) == 3
        sub_sections = {r.sub_section for r in result}
        assert sub_sections == {"1", "2", ""}

        # The empty sub_section should have both unnumbered paragraphs
        empty_subsection = [r for r in result if r.sub_section == ""][0]
        assert "Continuation of first" in empty_subsection.text
        assert "Another unnumbered" in empty_subsection.text

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_no_duplicate_keys_in_output(self, mock_requests, mock_extract_xml):
        """Output should never have duplicate (code, section, sub_section) tuples"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        # Create scenario that previously caused duplicates
        dokumente = self._create_mock_dokumente([
            {
                "enbez": "§ 1",
                "paragraphs": [
                    "Paragraph A without number.",
                    "Paragraph B without number.",
                    "Paragraph C without number.",
                ],
            },
            {
                "enbez": "§ 2",
                "paragraphs": [
                    "(1) Numbered paragraph.",
                    "Unnumbered paragraph.",
                ],
            },
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        # Check for uniqueness
        keys = [(r.code, r.section, r.sub_section) for r in result]
        assert len(keys) == len(set(keys)), "Duplicate keys found in output!"

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_skips_norms_without_enbez(self, mock_requests, mock_extract_xml):
        """Norms without enbez (section identifier) should be skipped"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        dokumente = self._create_mock_dokumente([
            {
                "enbez": None,  # No section identifier
                "paragraphs": ["Some text."],
            },
            {
                "enbez": "§ 1",
                "paragraphs": ["Valid section text."],
            },
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        assert len(result) == 1
        assert result[0].section == "§ 1"

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_uses_url_code_not_jurabk(self, mock_requests, mock_extract_xml):
        """Should use the code from URL, not from XML metadata"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        dokumente = self._create_mock_dokumente([
            {
                "jurabk": "BGB",  # XML says BGB
                "enbez": "§ 1",
                "paragraphs": ["Text."],
            },
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("my_custom_code")  # URL code

        assert result[0].code == "my_custom_code"


class TestExtractXmlFromZip:
    """Tests for _extract_xml_from_zip method"""

    def setup_method(self):
        self.scraper = GesetzteImInternetScraper()

    def _create_zip_with_xml(self, filename: str, content: bytes) -> bytes:
        """Helper to create a zip file in memory"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr(filename, content)
        return zip_buffer.getvalue()

    def test_extracts_xml_from_valid_zip(self):
        """Should extract XML content from a valid zip file"""
        xml_content = b"<?xml version='1.0'?><root>test</root>"
        zip_bytes = self._create_zip_with_xml("test.xml", xml_content)

        result = self.scraper._extract_xml_from_zip(zip_bytes)

        assert result == xml_content

    def test_extracts_first_file_from_zip(self):
        """Should extract the first file when zip contains multiple files"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("first.xml", b"first content")
            zf.writestr("second.xml", b"second content")
        zip_bytes = zip_buffer.getvalue()

        result = self.scraper._extract_xml_from_zip(zip_bytes)

        assert result == b"first content"

    def test_raises_on_invalid_zip(self):
        """Should raise error for invalid zip data"""
        with pytest.raises(zipfile.BadZipFile):
            self.scraper._extract_xml_from_zip(b"not a zip file")

    def test_raises_on_empty_zip(self):
        """Should raise error for empty zip file"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            pass  # Create empty zip
        zip_bytes = zip_buffer.getvalue()

        with pytest.raises(ValueError, match="contains no XML"):
            self.scraper._extract_xml_from_zip(zip_bytes)


class TestScrapeNetworkHandling:
    """Tests for network error handling in scrape method"""

    def setup_method(self):
        self.scraper = GesetzteImInternetScraper()

    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_constructs_correct_url(self, mock_requests):
        """Should construct correct URL from code"""
        mock_response = MagicMock()
        mock_response.content = b"fake"
        mock_requests.get.return_value = mock_response

        with patch.object(self.scraper, "_extract_xml_from_zip", side_effect=Exception("stop")):
            try:
                self.scraper.scrape("bgb")
            except:
                pass

        mock_requests.get.assert_called_once_with(
            "https://www.gesetze-im-internet.de/bgb/xml.zip", timeout=30
        )

    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_raises_on_http_error(self, mock_requests):
        """Should propagate HTTP errors (404, 500, etc.)"""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = HTTPError("404 Not Found")
        mock_requests.get.return_value = mock_response

        with pytest.raises(HTTPError):
            self.scraper.scrape("nonexistent_code")

    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_raises_on_connection_error(self, mock_requests):
        """Should propagate connection errors"""
        mock_requests.get.side_effect = ConnectionError("Connection refused")

        with pytest.raises(ConnectionError):
            self.scraper.scrape("bgb")

    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_raises_on_timeout(self, mock_requests):
        """Should propagate timeout errors"""
        mock_requests.get.side_effect = Timeout("Request timed out")

        with pytest.raises(Timeout):
            self.scraper.scrape("bgb")


class TestScrapeXmlParsing:
    """Tests for XML parsing integration"""

    def setup_method(self):
        self.scraper = GesetzteImInternetScraper()

    def _create_zip_with_xml(self, xml_content: bytes) -> bytes:
        """Helper to create a zip file with XML content"""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("legal.xml", xml_content)
        return zip_buffer.getvalue()

    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_parses_real_xml_structure(self, mock_requests):
        """Should correctly parse realistic XML structure"""
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <dokumente builddate="2024-01-01">
            <norm doknr="BJNR001950896BJNE000102377">
                <metadaten>
                    <jurabk>BGB</jurabk>
                    <enbez>\xc2\xa7 1</enbez>
                    <titel>Beginn der Rechtsf\xc3\xa4higkeit</titel>
                </metadaten>
                <textdaten>
                    <text format="XML">
                        <Content>
                            <P>Die Rechtsf\xc3\xa4higkeit des Menschen beginnt mit der Vollendung der Geburt.</P>
                        </Content>
                    </text>
                </textdaten>
            </norm>
        </dokumente>"""

        zip_bytes = self._create_zip_with_xml(xml_content)
        mock_response = MagicMock()
        mock_response.content = zip_bytes
        mock_requests.get.return_value = mock_response

        result = self.scraper.scrape("bgb")

        assert len(result) == 1
        assert result[0].code == "bgb"
        assert result[0].section == "§ 1"
        assert "Rechtsfähigkeit" in result[0].text

    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_handles_multiple_norms(self, mock_requests):
        """Should parse multiple norms from single document"""
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <dokumente>
            <norm>
                <metadaten>
                    <jurabk>BGB</jurabk>
                    <enbez>\xc2\xa7 1</enbez>
                </metadaten>
                <textdaten>
                    <text><Content><P>First section.</P></Content></text>
                </textdaten>
            </norm>
            <norm>
                <metadaten>
                    <jurabk>BGB</jurabk>
                    <enbez>\xc2\xa7 2</enbez>
                </metadaten>
                <textdaten>
                    <text><Content><P>Second section.</P></Content></text>
                </textdaten>
            </norm>
        </dokumente>"""

        zip_bytes = self._create_zip_with_xml(xml_content)
        mock_response = MagicMock()
        mock_response.content = zip_bytes
        mock_requests.get.return_value = mock_response

        result = self.scraper.scrape("bgb")

        assert len(result) == 2
        sections = {r.section for r in result}
        assert sections == {"§ 1", "§ 2"}

    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_handles_empty_document(self, mock_requests):
        """Should return empty list for document with no valid norms"""
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <dokumente>
        </dokumente>"""

        zip_bytes = self._create_zip_with_xml(xml_content)
        mock_response = MagicMock()
        mock_response.content = zip_bytes
        mock_requests.get.return_value = mock_response

        result = self.scraper.scrape("bgb")

        assert result == []


class TestScrapeEdgeCases:
    """Tests for edge cases in scraping"""

    def setup_method(self):
        self.scraper = GesetzteImInternetScraper()

    def _create_mock_dokumente(self, norms_data: list) -> Dokumente:
        """Helper to create Dokumente with specified norms"""
        norms = []
        for norm_data in norms_data:
            formatted_text = FormattedText(
                content="",
                paragraphs=norm_data.get("paragraphs", []),
            )
            text_content = TextContent(formatted_text=formatted_text)
            textdaten = Textdaten(text=text_content)
            metadaten = Metadaten(
                jurabk=[norm_data.get("jurabk", "BGB")],
                enbez=norm_data.get("enbez"),
            )
            norms.append(Norm(metadaten=metadaten, textdaten=textdaten))
        return Dokumente(norms=norms)

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_handles_norm_without_textdaten(self, mock_requests, mock_extract_xml):
        """Should skip norms that have no textdaten"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        # Create norm without textdaten
        norm = Norm(
            metadaten=Metadaten(jurabk=["BGB"], enbez="§ 1"),
            textdaten=None,
        )
        dokumente = Dokumente(norms=[norm])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        assert result == []

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_handles_norm_without_text(self, mock_requests, mock_extract_xml):
        """Should skip norms that have textdaten but no text"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        norm = Norm(
            metadaten=Metadaten(jurabk=["BGB"], enbez="§ 1"),
            textdaten=Textdaten(text=None),
        )
        dokumente = Dokumente(norms=[norm])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        assert result == []

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_handles_norm_without_formatted_text(self, mock_requests, mock_extract_xml):
        """Should skip norms that have text but no formatted_text"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        norm = Norm(
            metadaten=Metadaten(jurabk=["BGB"], enbez="§ 1"),
            textdaten=Textdaten(text=TextContent(formatted_text=None)),
        )
        dokumente = Dokumente(norms=[norm])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        assert result == []

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_handles_empty_paragraphs_list(self, mock_requests, mock_extract_xml):
        """Should handle norm with empty paragraphs list"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        dokumente = self._create_mock_dokumente([
            {
                "enbez": "§ 1",
                "paragraphs": [],  # Empty list
            },
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        assert result == []

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_handles_special_characters_in_text(self, mock_requests, mock_extract_xml):
        """Should preserve special characters (umlauts, etc.) in text"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        dokumente = self._create_mock_dokumente([
            {
                "enbez": "§ 1",
                "paragraphs": ["Die Rechtsfähigkeit des Menschen beginnt mit der Geburt."],
            },
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        assert "Rechtsfähigkeit" in result[0].text

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_preserves_paragraph_order_in_concatenation(self, mock_requests, mock_extract_xml):
        """Should preserve original paragraph order when concatenating"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        dokumente = self._create_mock_dokumente([
            {
                "enbez": "§ 1",
                "paragraphs": [
                    "First paragraph.",
                    "Second paragraph.",
                    "Third paragraph.",
                ],
            },
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        text = result[0].text
        first_pos = text.find("First")
        second_pos = text.find("Second")
        third_pos = text.find("Third")
        assert first_pos < second_pos < third_pos

    @patch.object(GesetzteImInternetScraper, "_extract_xml_from_zip")
    @patch("app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.requests")
    def test_handles_complex_subsection_patterns(self, mock_requests, mock_extract_xml):
        """Should handle various subsection numbering patterns"""
        mock_response = MagicMock()
        mock_response.content = b"fake zip"
        mock_requests.get.return_value = mock_response

        dokumente = self._create_mock_dokumente([
            {
                "enbez": "§ 1",
                "paragraphs": [
                    "(1) First subsection.",
                    "(1a) First-a subsection.",
                    "(2) Second subsection.",
                    "(10) Tenth subsection.",
                ],
            },
        ])

        with patch(
            "app.scrapers.gesetze_im_internet.gesetzte_im_internet_scraper.GermanLegalXMLParser"
        ) as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser.parse_bytes.return_value = dokumente
            mock_parser_class.return_value = mock_parser

            result = self.scraper.scrape("bgb")

        sub_sections = {r.sub_section for r in result}
        assert sub_sections == {"1", "1a", "2", "10"}
