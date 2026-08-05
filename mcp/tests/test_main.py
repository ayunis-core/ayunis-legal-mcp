"""Tests for multi-jurisdiction MCP query compatibility."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from server.main import get_available_codes, get_legal_section, search_legal_texts


def api_result(**overrides):
    result = {
        "text": "Legal text",
        "code": "shared",
        "source": "state-source",
        "jurisdiction": "DE-BY",
        "document_id": "opaque-42",
        "document_title": "Bayerisches Testgesetz",
        "document_type": "Gesetz",
        "source_url": "https://example.test/opaque-42",
        "build_date": "2026-08-05",
        "valid_from": None,
        "valid_to": None,
        "section": "Art. 1",
        "sub_section": "1",
        "similarity_score": 0.2,
    }
    result.update(overrides)
    return result


def async_client_with(payload):
    response = MagicMock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    client = AsyncMock()
    client.get.return_value = response
    context = AsyncMock()
    context.__aenter__.return_value = client
    context.__aexit__.return_value = None
    return context, client


@pytest.mark.asyncio
async def test_search_supports_jurisdiction_without_code():
    context, client = async_client_with({"results": [api_result()]})
    with patch("server.main.httpx.AsyncClient", return_value=context):
        results = await search_legal_texts.fn(
            query="Bauordnung",
            jurisdiction="DE-BY",
            code=None,
            source=None,
            document_id=None,
            limit=5,
            cutoff=0.7,
        )

    assert results[0].jurisdiction == "DE-BY"
    assert results[0].source_url == "https://example.test/opaque-42"
    call = client.get.await_args
    assert call.args[0].endswith("/legal-texts/search")
    assert call.kwargs["params"]["jurisdiction"] == "DE-BY"
    assert "code" not in call.kwargs["params"]


@pytest.mark.asyncio
async def test_federal_code_search_remains_compatible():
    context, client = async_client_with(
        {"results": [api_result(code="bgb", jurisdiction="DE")]}
    )
    with patch("server.main.httpx.AsyncClient", return_value=context):
        results = await search_legal_texts.fn(
            query="Vertrag",
            jurisdiction="DE",
            code="bgb",
            source=None,
            document_id=None,
            limit=5,
            cutoff=0.7,
        )

    assert results[0].code == "bgb"
    assert client.get.await_args.kwargs["params"]["code"] == "bgb"


@pytest.mark.asyncio
async def test_exact_section_uses_source_independent_api():
    context, client = async_client_with({"results": [api_result()]})
    with patch("server.main.httpx.AsyncClient", return_value=context):
        results = await get_legal_section.fn(
            code="shared",
            section="Art. 1",
            jurisdiction="DE-BY",
            source="state-source",
            document_id="opaque-42",
            sub_section="1",
        )

    assert results[0].document_title == "Bayerisches Testgesetz"
    call = client.get.await_args
    assert call.args[0].endswith("/legal-texts")
    assert call.kwargs["params"]["document_id"] == "opaque-42"


@pytest.mark.asyncio
async def test_available_codes_can_be_filtered_by_jurisdiction_and_source():
    context, client = async_client_with({"codes": ["BayTest"]})
    with patch("server.main.httpx.AsyncClient", return_value=context):
        codes = await get_available_codes.fn(
            jurisdiction="DE-BY", source="state-source"
        )

    assert codes == ["BayTest"]
    call = client.get.await_args
    assert call.args[0].endswith("/legal-texts/codes")
    assert call.kwargs["params"] == {
        "jurisdiction": "DE-BY",
        "source": "state-source",
    }
