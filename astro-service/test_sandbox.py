# -*- coding: utf-8 -*-
"""Tests for sandbox-specific endpoints."""
from unittest.mock import ANY, MagicMock, patch

import pytest
from fastapi import HTTPException as FastHTTPException
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

SAMPLE_MATCH_DATA = {
    "lust_score": 82.0,
    "soul_score": 71.0,
    "power": {"rpv": 25.0, "frame_break": False, "viewer_role": "Dom", "target_role": "Sub"},
    "tracks": {"friend": 45.0, "passion": 78.0, "partner": 62.0, "soul": 55.0},
    "primary_track": "passion",
    "quadrant": "lover",
    "labels": ["✦ 激情型連結"],
}


def test_generate_archetype_returns_tags_and_report():
    """Endpoint returns archetype_tags list + report string."""
    fake_json = '{"archetype_tags": ["Mirror Twins", "Power Clash", "Slow Burn"], "report": "This is a test report with more than ten characters."}'

    with patch("main.call_llm", return_value=fake_json):
        resp = client.post("/generate-archetype", json={
            "match_data": SAMPLE_MATCH_DATA,
            "person_a_name": "Person A",
            "person_b_name": "Person B",
            "provider": "anthropic",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "archetype_tags" in data
    assert "report" in data
    assert isinstance(data["archetype_tags"], list)
    assert len(data["archetype_tags"]) == 3
    assert isinstance(data["report"], str)
    assert len(data["report"]) > 10


def test_generate_archetype_gemini_provider():
    """Endpoint works with gemini provider too."""
    fake_json = '{"archetype_tags": ["Fire Duo", "Deep Pull", "Mirror Bond"], "report": "Gemini generated report content"}'

    with patch("main.call_llm", return_value=fake_json) as mock_llm:
        resp = client.post("/generate-archetype", json={
            "match_data": SAMPLE_MATCH_DATA,
            "provider": "gemini",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["archetype_tags"]) == 3
    # Verify provider was passed through to call_llm
    mock_llm.assert_called_once_with(ANY, provider="gemini", max_tokens=ANY)


def test_generate_archetype_no_api_key_returns_400():
    """Returns 400 when ANTHROPIC_API_KEY is not set."""
    with patch("main.call_llm", side_effect=FastHTTPException(status_code=400, detail="ANTHROPIC_API_KEY not set")):
        resp = client.post("/generate-archetype", json={
            "match_data": SAMPLE_MATCH_DATA,
        })
    assert resp.status_code == 400
    assert "ANTHROPIC_API_KEY" in resp.json()["detail"]
