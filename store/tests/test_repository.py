"""
Unit tests for LegalTextRepository
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.repository import LegalTextRepository, LegalTextFilter
from app.models import LegalTextDB

pytestmark = pytest.mark.unit


@pytest.fixture
def mock_session():
    """Create a mock async session"""
    session = AsyncMock()
    return session


@pytest.fixture
def repository(mock_session):
    """Create a repository with mock session"""
    return LegalTextRepository(mock_session)


class TestLegalTextFilter:
    """Tests for LegalTextFilter validation"""

    def test_filter_with_code_only(self):
        """Test filter with only code"""
        filter = LegalTextFilter(code="bgb")
        assert filter.code == "bgb"
        assert filter.section is None
        assert filter.sub_section is None

    def test_filter_with_code_and_section(self):
        """Test filter with code and section"""
        filter = LegalTextFilter(code="bgb", section="§ 1")
        assert filter.code == "bgb"
        assert filter.section == "§ 1"
        assert filter.sub_section is None

    def test_filter_with_all_fields(self):
        """Test filter with all fields"""
        filter = LegalTextFilter(code="bgb", section="§ 1", sub_section="1")
        assert filter.code == "bgb"
        assert filter.section == "§ 1"
        assert filter.sub_section == "1"

    def test_filter_rejects_sub_section_without_section(self):
        """Test that sub_section without section raises validation error"""
        with pytest.raises(ValueError, match="sub_section filter can only be used when section filter is also provided"):
            LegalTextFilter(code="bgb", sub_section="1")


class TestLegalTextRepository:
    """Tests for LegalTextRepository methods"""

    @pytest.mark.asyncio
    async def test_get_legal_text_with_code_only(self, repository, mock_session):
        """Test getting legal texts filtered by code only"""
        # Setup mock
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [
            LegalTextDB(id=1, text="Test", code="bgb", section="§ 1", sub_section="1", text_vector=[0.1] * 2560)
        ]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Execute
        filter = LegalTextFilter(code="bgb")
        result = await repository.get_legal_text(filter)

        # Verify
        assert len(result) == 1
        assert result[0].code == "bgb"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_legal_text_with_code_and_section(self, repository, mock_session):
        """Test getting legal texts filtered by code and section"""
        # Setup mock
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [
            LegalTextDB(id=1, text="Test", code="bgb", section="§ 1", sub_section="1", text_vector=[0.1] * 2560)
        ]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Execute
        filter = LegalTextFilter(code="bgb", section="§ 1")
        result = await repository.get_legal_text(filter)

        # Verify
        assert len(result) == 1
        assert result[0].section == "§ 1"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_legal_text_returns_empty_list(self, repository, mock_session):
        """Test getting legal texts when none match"""
        # Setup mock
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Execute
        filter = LegalTextFilter(code="nonexistent")
        result = await repository.get_legal_text(filter)

        # Verify
        assert result == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_legal_text(self, repository, mock_session):
        """Test adding a single legal text"""
        # Setup
        legal_text = LegalTextDB(
            text="Test text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )

        # Execute
        result = await repository.add_legal_text(legal_text)

        # Verify
        mock_session.add.assert_called_once_with(legal_text)
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once_with(legal_text)
        assert result == legal_text

    @pytest.mark.asyncio
    async def test_add_legal_texts_batch_empty_list(self, repository, mock_session):
        """Test adding empty batch returns empty list"""
        # Execute
        result = await repository.add_legal_texts_batch([])

        # Verify
        assert result == []
        mock_session.execute.assert_not_called()
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_add_legal_texts_batch(self, repository, mock_session):
        """Test adding multiple legal texts in batch"""
        # Setup
        legal_texts = [
            LegalTextDB(
                text="Text 1",
                code="bgb",
                section="§ 1",
                sub_section="1",
                text_vector=[0.1] * 2560
            ),
            LegalTextDB(
                text="Text 2",
                code="bgb",
                section="§ 2",
                sub_section="1",
                text_vector=[0.2] * 2560
            ),
        ]

        # Execute
        result = await repository.add_legal_texts_batch(legal_texts)

        # Verify
        assert result == legal_texts
        mock_session.execute.assert_called_once()
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_by_code(self, repository, mock_session):
        """Test counting legal texts by code"""
        # Setup mock
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [MagicMock(), MagicMock(), MagicMock()]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Execute
        count = await repository.count_by_code("bgb")

        # Verify
        assert count == 3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_codes_returns_empty_list_when_no_data(self, repository, mock_session):
        """Test getting available codes when database is empty"""
        # Setup mock
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Execute
        codes = await repository.get_available_codes()

        # Verify
        assert codes == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_available_codes_returns_sorted_codes(self, repository, mock_session):
        """Test getting available codes returns sorted list"""
        # Setup mock
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = ["bgb", "gg", "stgb"]
        mock_result.scalars.return_value = mock_scalars
        mock_session.execute.return_value = mock_result

        # Execute
        codes = await repository.get_available_codes()

        # Verify
        assert codes == ["bgb", "gg", "stgb"]
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search_with_cutoff(self, repository, mock_session):
        """Test semantic search with cutoff threshold"""
        # Setup mock
        mock_legal_text = LegalTextDB(
            id=1,
            text="Test text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_legal_text, 0.5)]
        mock_session.execute.return_value = mock_result

        # Execute
        query_embedding = [0.2] * 2560
        results = await repository.semantic_search(
            query_embedding=query_embedding,
            code="bgb",
            limit=10,
            cutoff=0.7
        )

        # Verify
        assert len(results) == 1
        assert results[0][0] == mock_legal_text
        assert results[0][1] == 0.5
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search_without_cutoff(self, repository, mock_session):
        """Test semantic search without cutoff threshold"""
        # Setup mock
        mock_legal_text = LegalTextDB(
            id=1,
            text="Test text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_legal_text, 0.3)]
        mock_session.execute.return_value = mock_result

        # Execute
        query_embedding = [0.2] * 2560
        results = await repository.semantic_search(
            query_embedding=query_embedding,
            code="bgb",
            limit=5
        )

        # Verify
        assert len(results) == 1
        assert results[0][0] == mock_legal_text
        assert results[0][1] == 0.3
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search_returns_empty_list(self, repository, mock_session):
        """Test semantic search with no results"""
        # Setup mock
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_session.execute.return_value = mock_result

        # Execute
        query_embedding = [0.2] * 2560
        results = await repository.semantic_search(
            query_embedding=query_embedding,
            code="bgb",
            limit=10
        )

        # Verify
        assert results == []
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search_without_code(self, repository, mock_session):
        """Test semantic search without code filter (searches all codes)"""
        # Setup mock
        mock_legal_text_bgb = LegalTextDB(
            id=1,
            text="BGB Test text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_legal_text_stgb = LegalTextDB(
            id=2,
            text="StGB Test text",
            code="stgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.2] * 2560
        )
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_legal_text_bgb, 0.3), (mock_legal_text_stgb, 0.5)]
        mock_session.execute.return_value = mock_result

        # Execute - no code parameter
        query_embedding = [0.2] * 2560
        results = await repository.semantic_search(
            query_embedding=query_embedding,
            limit=10
        )

        # Verify
        assert len(results) == 2
        assert results[0][0].code == "bgb"
        assert results[1][0].code == "stgb"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_semantic_search_with_code_none(self, repository, mock_session):
        """Test semantic search with code explicitly set to None"""
        # Setup mock
        mock_legal_text = LegalTextDB(
            id=1,
            text="Test text",
            code="bgb",
            section="§ 1",
            sub_section="1",
            text_vector=[0.1] * 2560
        )
        mock_result = MagicMock()
        mock_result.all.return_value = [(mock_legal_text, 0.3)]
        mock_session.execute.return_value = mock_result

        # Execute with code=None
        query_embedding = [0.2] * 2560
        results = await repository.semantic_search(
            query_embedding=query_embedding,
            code=None,
            limit=10
        )

        # Verify
        assert len(results) == 1
        mock_session.execute.assert_called_once()
