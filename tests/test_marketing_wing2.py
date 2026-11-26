"""Tests for Wing 2 — Kilobyte Labs Marketing & Growth Engine."""
from __future__ import annotations

from agent_house.marketing_graph import generate_platform_campaigns, verify_campaign_copy


def test_wing2_marketing_campaigns_pass_growth_verifier_100() -> None:
    payload = generate_platform_campaigns()
    assert payload["brand"] == "Kilobyte Labs"
    assert len(payload["campaigns"]) >= 5
    for camp in payload["campaigns"]:
        assert camp["qa"]["pass"] is True, f"Campaign failed QA: {camp['campaign_id']} -> {camp['qa']}"
        assert camp["qa"]["score"] == 100


def test_growth_verifier_blocks_spam_and_undisclosed_hype() -> None:
    spam = {
        "title": "BUY NOW!!! MIRACLE APP 100% GUARANTEED TO GET RICH",
        "body": "Best app ever, trust me bro!",
        "cta_urls": [],
    }
    res = verify_campaign_copy(spam)
    assert res["pass"] is False
    assert res["score"] < 50
