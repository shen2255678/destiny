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


def test_generate_profile_card_returns_card():
    """Profile card endpoint returns required fields."""
    fake_json = '{"headline": "\u63a2\u7d22\u8005\u578b", "tags": ["\u76f4\u89ba\u654f\u9280", "\u60c5\u611f\u6df1\u5ea6", "\u559c\u6b61\u5b89\u975c\u7684\u9a5a\u559c"], "bio": "\u4f60\u662f\u90a3\u7a2e\u559c\u6b61\u7dca\u8ddf\u6642\u4ee3\u4f46\u4e0d\u8ddf\u6e6e\u6d41\u884c\u7684\u4eba\u3002\u6df1\u5ea6\u3001\u76f4\u89ba\u3001\u81ea\u5c71\u3002", "vibe_keywords": ["\u795e\u79d8", "\u6eab\u67d4", "\u7368\u7acb"]}'

    with patch("main.call_llm", return_value=fake_json):
        resp = client.post("/generate-profile-card", json={
            "chart_data": {
                "sun_sign": "gemini", "moon_sign": "pisces",
                "ascendant_sign": "virgo", "bazi_element": "wood",
                "data_tier": 1
            },
            "rpv_data": {
                "rpv_conflict": "cold_war",
                "rpv_power": "control",
                "rpv_energy": "home"
            },
            "attachment_style": "anxious",
            "provider": "anthropic",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "headline" in data
    assert "tags" in data
    assert "bio" in data
    assert "vibe_keywords" in data
    assert isinstance(data["tags"], list)
    assert len(data["tags"]) >= 3
    assert isinstance(data["bio"], str)
    assert len(data["bio"]) > 10


def test_generate_match_report_returns_report():
    fake_json = '{"title": "\u6fc0\u60c5\u578b\u9023\u7d50", "sparks": ["\u9748\u9b42\u5171\u9cf4\u6df1\u5ea6", "\u4e92\u88dc\u7684\u80fd\u91cf\u6d41\u52d5"], "landmines": ["\u63a7\u5236\u6b32\u5f35\u529b"], "advice": "\u4fdd\u6301\u5404\u81ea\u7a7a\u9593\uff0c\u5b9a\u671f\u6df1\u5ea6\u5c0d\u8a71\u3002", "one_liner": "\u4f60\u5011\u662f\u5f7c\u6b64\u7684\u93e1\u5b50\uff0c\u4e5f\u662f\u5f7c\u6b64\u7684\u706b\u7130\u3002"}'

    with patch("main.call_llm", return_value=fake_json):
        resp = client.post("/generate-match-report", json={
            "match_data": SAMPLE_MATCH_DATA,
            "person_a_name": "Alice",
            "person_b_name": "Bob",
            "provider": "anthropic",
        })

    assert resp.status_code == 200
    data = resp.json()
    assert "title" in data
    assert "sparks" in data
    assert "landmines" in data
    assert "advice" in data
    assert "one_liner" in data
    assert len(data["sparks"]) >= 1
