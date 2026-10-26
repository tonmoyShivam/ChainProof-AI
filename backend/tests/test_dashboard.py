"""Dashboard stats must come from real DB counts."""

from __future__ import annotations

from tests.conftest import register_and_login


def test_dashboard_stats_start_at_zero(client) -> None:
    token = register_and_login(client)
    response = client.get(
        "/api/v1/dashboard/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total_registered_models"] == 0
    assert body["total_verification_attempts"] == 0
    assert body["successful_verifications"] == 0
    assert body["integrity_mismatches"] == 0


def test_recent_activity_empty(client) -> None:
    token = register_and_login(client)
    response = client.get(
        "/api/v1/dashboard/recent-activity",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json() == []
