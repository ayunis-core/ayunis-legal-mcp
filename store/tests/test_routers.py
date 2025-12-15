"""
Unit tests for legal texts router endpoints
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.main import app
from app.models import LegalTextDB, LegalText
from app.repository import LegalTextRepository
from app.dependencies import get_legal_text_repository, get_embedding_service_dependency

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_repository():
    """Create a mock repository"""
    return AsyncMock(spec=LegalTextRepository)


@pytest.fixture
def mock_embedding_service():
    """Create a mock embedding service"""
    service = AsyncMock()
    service.generate_embeddings = AsyncMock()
    return service


@pytest.fixture
def client_with_mocks(mock_repository, mock_embedding_service):
    """Create a test client with mocked dependencies"""
    app.dependency_overrides[get_legal_text_repository] = lambda: mock_repository
    app.dependency_overrides[get_embedding_service_dependency] = lambda: mock_embedding_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


class TestGetAvailableCodes:
    """Tests for GET /legal-texts/gesetze-im-internet/codes endpoint"""

    def test_get_available_codes_returns_empty_list(self, client_with_mocks, mock_repository):
        """Test endpoint returns empty list when no codes exist"""
        mock_repository.get_available_codes.return_value = []
        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/codes")

        assert response.status_code == 200
        assert response.json() == {"codes": []}

    def test_get_available_codes_returns_codes_list(self, client_with_mocks, mock_repository):
        """Test endpoint returns list of available codes"""
        mock_repository.get_available_codes.return_value = ["bgb", "gg", "stgb"]
        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/codes")

        assert response.status_code == 200
        assert response.json() == {"codes": ["bgb", "gg", "stgb"]}

    def test_get_available_codes_handles_repository_error(self, client_with_mocks, mock_repository):
        """Test endpoint handles repository errors gracefully"""
        mock_repository.get_available_codes.side_effect = Exception("Database error")
        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/codes")

        assert response.status_code == 500
        assert "Error fetching available codes" in response.json()["detail"]


class TestGetLegalTexts:
    """Tests for GET /legal-texts/gesetze-im-internet/{code} endpoint"""

    def test_get_legal_texts_by_code(self, client_with_mocks, mock_repository):
        """Test getting legal texts by code only"""
        mock_legal_text = LegalTextDB(
            id=1,
            text="Test text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_repository.get_legal_text.return_value = [mock_legal_text]
        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["code"] == "bgb"
        assert data["results"][0]["text"] == "Test text"

    def test_get_legal_texts_by_code_and_section(self, client_with_mocks, mock_repository):
        """Test getting legal texts filtered by code and section"""
        mock_legal_text = LegalTextDB(
            id=1,
            text="Test text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_repository.get_legal_text.return_value = [mock_legal_text]
        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb?section=§ 1")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["results"][0]["section"] == "§ 1"

    def test_get_legal_texts_with_sub_section_without_section_returns_400(self, client_with_mocks, mock_repository):
        """Test that providing sub_section without section returns 400 error"""
        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb?sub_section=1")

        assert response.status_code == 400
        assert "sub_section filter can only be used when section filter is also provided" in response.json()["detail"]

    def test_get_legal_texts_returns_404_when_none_found(self, client_with_mocks, mock_repository):
        """Test endpoint returns 404 when no texts found"""
        mock_repository.get_legal_text.return_value = []
        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/nonexistent")

        assert response.status_code == 404
        assert "No legal texts found" in response.json()["detail"]

    def test_get_legal_texts_handles_repository_error(self, client_with_mocks, mock_repository):
        """Test endpoint handles repository errors"""
        mock_repository.get_legal_text.side_effect = Exception("Database error")
        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb")

        assert response.status_code == 500
        assert "Error querying legal texts" in response.json()["detail"]


class TestGlobalSemanticSearch:
    """Tests for GET /legal-texts/search endpoint (global search)"""

    def test_global_search_without_code_returns_results(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test global search returns results from all codes when no code specified"""
        # Setup mocks
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]

        mock_legal_text_bgb = LegalTextDB(
            id=1,
            text="Contract law text BGB",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_legal_text_stgb = LegalTextDB(
            id=2,
            text="Contract law text StGB",
            code="stgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.2] * 2560
        )
        mock_repository.semantic_search.return_value = [(mock_legal_text_bgb, 0.3), (mock_legal_text_stgb, 0.5)]

        response = client_with_mocks.get("/legal-texts/search?q=Vertragsrecht")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Vertragsrecht"
        assert data["code"] is None  # No code filter
        assert data["count"] == 2
        assert len(data["results"]) == 2
        # Verify repository was called without code filter
        mock_repository.semantic_search.assert_called_once()
        call_args = mock_repository.semantic_search.call_args
        assert call_args.kwargs["code"] is None

    def test_global_search_with_code_returns_filtered_results(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test global search filters by code when code is specified"""
        # Setup mocks
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]

        mock_legal_text = LegalTextDB(
            id=1,
            text="Contract law text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_repository.semantic_search.return_value = [(mock_legal_text, 0.3)]

        response = client_with_mocks.get("/legal-texts/search?q=Vertragsrecht&code=bgb")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Vertragsrecht"
        assert data["code"] == "bgb"
        assert data["count"] == 1
        # Verify repository was called with code filter
        mock_repository.semantic_search.assert_called_once()
        call_args = mock_repository.semantic_search.call_args
        assert call_args.kwargs["code"] == "bgb"

    def test_global_search_with_custom_limit(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test global search respects limit parameter"""
        # Setup mocks
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
        mock_repository.semantic_search.return_value = []

        response = client_with_mocks.get("/legal-texts/search?q=test&limit=5")

        assert response.status_code == 200
        # Verify repository was called with correct limit
        mock_repository.semantic_search.assert_called_once()
        call_args = mock_repository.semantic_search.call_args
        assert call_args.kwargs["limit"] == 5

    def test_global_search_with_custom_cutoff(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test global search respects cutoff parameter"""
        # Setup mocks
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
        mock_repository.semantic_search.return_value = []

        response = client_with_mocks.get("/legal-texts/search?q=test&cutoff=0.5")

        assert response.status_code == 200
        # Verify repository was called with correct cutoff
        call_args = mock_repository.semantic_search.call_args
        assert call_args.kwargs["cutoff"] == 0.5

    def test_global_search_handles_embedding_error(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test global search handles embedding generation errors"""
        mock_embedding_service.generate_embeddings.side_effect = Exception("Ollama connection error")

        response = client_with_mocks.get("/legal-texts/search?q=test")

        assert response.status_code == 500
        assert "Error generating query embedding" in response.json()["detail"]

    def test_global_search_handles_repository_error(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test global search handles repository errors"""
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
        mock_repository.semantic_search.side_effect = Exception("Database error")

        response = client_with_mocks.get("/legal-texts/search?q=test")

        assert response.status_code == 500
        assert "Error performing semantic search" in response.json()["detail"]


class TestSemanticSearchLegalTexts:
    """Tests for GET /legal-texts/gesetze-im-internet/{code}/search endpoint"""

    def test_semantic_search_returns_results(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test semantic search returns matching results"""
        # Setup mocks
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]

        mock_legal_text = LegalTextDB(
            id=1,
            text="Contract law text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_repository.semantic_search.return_value = [(mock_legal_text, 0.3)]

        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb/search?q=Vertragsrecht")

        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Vertragsrecht"
        assert data["code"] == "bgb"
        assert data["count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["text"] == "Contract law text"
        assert data["results"][0]["similarity_score"] == 0.3

    def test_semantic_search_with_custom_limit(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test semantic search respects limit parameter"""
        # Setup mocks
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
        mock_repository.semantic_search.return_value = []

        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb/search?q=test&limit=5")

        assert response.status_code == 200
        # Verify repository was called with correct limit
        mock_repository.semantic_search.assert_called_once()
        call_args = mock_repository.semantic_search.call_args
        assert call_args.kwargs["limit"] == 5

    def test_semantic_search_with_custom_cutoff(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test semantic search respects cutoff parameter"""
        # Setup mocks
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
        mock_repository.semantic_search.return_value = []

        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb/search?q=test&cutoff=0.5")

        assert response.status_code == 200
        # Verify repository was called with correct cutoff
        call_args = mock_repository.semantic_search.call_args
        assert call_args.kwargs["cutoff"] == 0.5

    def test_semantic_search_returns_empty_results(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test semantic search returns empty array when no matches"""
        # Setup mocks
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
        mock_repository.semantic_search.return_value = []

        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb/search?q=nonexistent")

        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["results"] == []

    def test_semantic_search_handles_embedding_error(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test semantic search handles embedding generation errors"""
        mock_embedding_service.generate_embeddings.side_effect = Exception("Ollama connection error")

        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb/search?q=test")

        assert response.status_code == 500
        assert "Error generating query embedding" in response.json()["detail"]

    def test_semantic_search_handles_repository_error(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test semantic search handles repository errors"""
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
        mock_repository.semantic_search.side_effect = Exception("Database error")

        response = client_with_mocks.get("/legal-texts/gesetze-im-internet/bgb/search?q=test")

        assert response.status_code == 500
        assert "Error performing semantic search" in response.json()["detail"]


class TestImportLegalText:
    """Tests for POST /legal-texts/gesetze-im-internet/{book} endpoint"""

    def test_import_legal_text_success(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test successful legal text import"""
        # Setup mocks
        legal_texts = [
            LegalText(text="Text 1", code="bgb", section="§ 1", sub_section="1"),
            LegalText(text="Text 2", code="bgb", section="§ 2", sub_section="1"),
        ]
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560, [0.2] * 2560]
        mock_repository.add_legal_texts_batch.return_value = []

        with patch('app.routers.legal_texts.GesetzteImInternetCatalog') as mock_catalog_class, \
             patch('app.routers.legal_texts.GesetzteImInternetScraper') as mock_scraper_class:

            # Mock catalog validation to pass
            mock_catalog = MagicMock()
            mock_catalog.is_valid_code.return_value = True
            mock_catalog_class.return_value = mock_catalog

            # Mock scraper
            mock_scraper = MagicMock()
            mock_scraper.scrape.return_value = legal_texts
            mock_scraper_class.return_value = mock_scraper

            response = client_with_mocks.post("/legal-texts/gesetze-im-internet/bgb")

            assert response.status_code == 200
            data = response.json()
            assert data["code"] == "bgb"
            assert data["texts_imported"] == 2
            assert "Successfully imported" in data["message"]

    def test_import_legal_text_handles_scraping_error(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test import handles scraping errors"""
        with patch('app.routers.legal_texts.GesetzteImInternetCatalog') as mock_catalog_class, \
             patch('app.routers.legal_texts.GesetzteImInternetScraper') as mock_scraper_class:

            # Mock catalog validation to pass
            mock_catalog = MagicMock()
            mock_catalog.is_valid_code.return_value = True
            mock_catalog_class.return_value = mock_catalog

            # Mock scraper to fail
            mock_scraper = MagicMock()
            mock_scraper.scrape.side_effect = Exception("Network error")
            mock_scraper_class.return_value = mock_scraper

            response = client_with_mocks.post("/legal-texts/gesetze-im-internet/bgb")

            assert response.status_code == 500
            assert "Error importing document" in response.json()["detail"]

    def test_import_legal_text_returns_404_when_no_texts_found(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test import returns 404 when scraper finds no texts"""
        with patch('app.routers.legal_texts.GesetzteImInternetCatalog') as mock_catalog_class, \
             patch('app.routers.legal_texts.GesetzteImInternetScraper') as mock_scraper_class:

            # Mock catalog validation to pass
            mock_catalog = MagicMock()
            mock_catalog.is_valid_code.return_value = True
            mock_catalog_class.return_value = mock_catalog

            # Mock scraper to return empty list
            mock_scraper = MagicMock()
            mock_scraper.scrape.return_value = []
            mock_scraper_class.return_value = mock_scraper

            response = client_with_mocks.post("/legal-texts/gesetze-im-internet/nonexistent")

            assert response.status_code == 404
            assert "No legal texts found" in response.json()["detail"]

    def test_import_legal_text_handles_embedding_error(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test import handles embedding generation errors"""
        legal_texts = [
            LegalText(text="Text 1", code="bgb", section="§ 1", sub_section="1")
        ]
        mock_embedding_service.generate_embeddings.side_effect = Exception("Ollama not available")

        with patch('app.routers.legal_texts.GesetzteImInternetCatalog') as mock_catalog_class, \
             patch('app.routers.legal_texts.GesetzteImInternetScraper') as mock_scraper_class:

            # Mock catalog validation to pass
            mock_catalog = MagicMock()
            mock_catalog.is_valid_code.return_value = True
            mock_catalog_class.return_value = mock_catalog

            # Mock scraper
            mock_scraper = MagicMock()
            mock_scraper.scrape.return_value = legal_texts
            mock_scraper_class.return_value = mock_scraper

            response = client_with_mocks.post("/legal-texts/gesetze-im-internet/bgb")

            assert response.status_code == 500
            assert "Error generating embeddings" in response.json()["detail"]
            assert "Make sure Ollama is running" in response.json()["detail"]

    def test_import_invalid_code(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test import rejects invalid code from catalog"""
        with patch('app.routers.legal_texts.GesetzteImInternetCatalog') as mock_catalog_class:
            mock_catalog = MagicMock()
            mock_catalog.is_valid_code.return_value = False
            mock_catalog_class.return_value = mock_catalog

            response = client_with_mocks.post("/legal-texts/gesetze-im-internet/invalid_code")

            assert response.status_code == 400
            assert "Invalid legal code" in response.json()["detail"]
            assert "/catalog endpoint" in response.json()["detail"]

    def test_import_catalog_validation_fails_gracefully(self, client_with_mocks, mock_repository, mock_embedding_service):
        """Test import proceeds if catalog validation fails"""
        from app.scrapers import CatalogFetchError

        legal_texts = [
            LegalText(text="Text 1", code="bgb", section="§ 1", sub_section="1"),
        ]
        mock_embedding_service.generate_embeddings.return_value = [[0.1] * 2560]
        mock_repository.add_legal_texts_batch.return_value = []

        with patch('app.routers.legal_texts.GesetzteImInternetCatalog') as mock_catalog_class, \
             patch('app.routers.legal_texts.GesetzteImInternetScraper') as mock_scraper_class:

            # Catalog validation fails
            mock_catalog = MagicMock()
            mock_catalog.is_valid_code.side_effect = CatalogFetchError("Network error")
            mock_catalog_class.return_value = mock_catalog

            # But scraper succeeds
            mock_scraper = MagicMock()
            mock_scraper.scrape.return_value = legal_texts
            mock_scraper_class.return_value = mock_scraper

            response = client_with_mocks.post("/legal-texts/gesetze-im-internet/bgb")

            # Should succeed despite catalog validation failure
            assert response.status_code == 200
            assert response.json()["texts_imported"] == 1


class TestGetImportableCatalog:
    """Tests for GET /legal-texts/gesetze-im-internet/catalog endpoint"""

    def test_get_catalog_success(self, client_with_mocks):
        """Test catalog endpoint returns list of importable codes"""
        from app.scrapers import LegalCodeCatalogEntry

        mock_entries = [
            LegalCodeCatalogEntry(
                code="bgb",
                title="Bürgerliches Gesetzbuch",
                url="https://www.gesetze-im-internet.de/bgb/xml.zip"
            ),
            LegalCodeCatalogEntry(
                code="stgb",
                title="Strafgesetzbuch",
                url="https://www.gesetze-im-internet.de/stgb/xml.zip"
            ),
        ]

        with patch('app.routers.legal_texts.GesetzteImInternetCatalog') as mock_catalog_class:
            mock_catalog = MagicMock()
            mock_catalog.get_catalog.return_value = mock_entries
            mock_catalog_class.return_value = mock_catalog

            response = client_with_mocks.get("/legal-texts/gesetze-im-internet/catalog")

            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
            assert len(data["entries"]) == 2
            assert data["entries"][0]["code"] == "bgb"
            assert data["entries"][0]["title"] == "Bürgerliches Gesetzbuch"
            assert data["entries"][0]["url"] == "https://www.gesetze-im-internet.de/bgb/xml.zip"

    def test_get_catalog_error(self, client_with_mocks):
        """Test catalog endpoint handles errors"""
        with patch('app.routers.legal_texts.GesetzteImInternetCatalog') as mock_catalog_class:
            mock_catalog = MagicMock()
            mock_catalog.get_catalog.side_effect = Exception("Network error")
            mock_catalog_class.return_value = mock_catalog

            response = client_with_mocks.get("/legal-texts/gesetze-im-internet/catalog")

            assert response.status_code == 500
            assert "Error fetching catalog" in response.json()["detail"]
