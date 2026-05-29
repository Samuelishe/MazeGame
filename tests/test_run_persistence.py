from __future__ import annotations

from pathlib import Path

from highscores import Highscore, load_highscore, save_highscore
from runtime.run_persistence import handle_run_persistence
from runtime.session_stats import SessionStats
from session_controller import RunResult


class _FakeController:
    def __init__(self) -> None:
        self.recorded_results: list[RunResult] = []

    def record_run(self, result: RunResult) -> None:
        self.recorded_results.append(result)


def test_handle_run_persistence_updates_highscore_and_standalone_stats(tmp_path: Path) -> None:
    highscore_path = tmp_path / "highscore.json"
    highscore = Highscore()
    stats = SessionStats()

    handle_run_persistence(
        highscore=highscore,
        highscore_json_path=str(highscore_path),
        stats=stats,
        session_controller=None,
        active_player_id=None,
        score=320,
        elapsed_ms=7_500,
        coins_value_sum=14,
        won=True,
        bronze_count=2,
        silver_count=1,
        gold_count=1,
        diamond_count=1,
    )

    saved = load_highscore(str(highscore_path))

    assert saved == Highscore(
        best_score=320,
        max_coins_value=14,
        best_time_ms=7_500,
        bronze_max=2,
        silver_max=1,
        gold_max=1,
        diamond_max=1,
    )
    assert stats.runs == 1
    assert stats.wins == 1
    assert stats.deaths == 0
    assert stats.total_score == 320
    assert stats.total_time_ms == 7_500
    assert stats.total_coins == 14
    assert stats.bronze_total == 2
    assert stats.silver_total == 1
    assert stats.gold_total == 1
    assert stats.diamond_total == 1


def test_handle_run_persistence_does_not_rewrite_highscore_when_result_is_worse(tmp_path: Path) -> None:
    highscore_path = tmp_path / "highscore.json"
    initial_highscore = Highscore(
        best_score=500,
        max_coins_value=20,
        best_time_ms=6_000,
        bronze_max=3,
        silver_max=2,
        gold_max=1,
        diamond_max=1,
    )
    save_highscore(initial_highscore, str(highscore_path))
    before = highscore_path.read_text(encoding="utf-8")

    stats = SessionStats()
    highscore = load_highscore(str(highscore_path))

    handle_run_persistence(
        highscore=highscore,
        highscore_json_path=str(highscore_path),
        stats=stats,
        session_controller=None,
        active_player_id=None,
        score=100,
        elapsed_ms=9_000,
        coins_value_sum=5,
        won=False,
        bronze_count=1,
        silver_count=0,
        gold_count=0,
        diamond_count=0,
    )

    after = highscore_path.read_text(encoding="utf-8")
    saved = load_highscore(str(highscore_path))

    assert after == before
    assert saved == initial_highscore
    assert stats.runs == 1
    assert stats.wins == 0
    assert stats.deaths == 1
    assert stats.total_score == 100
    assert stats.total_time_ms == 9_000
    assert stats.total_coins == 5


def test_handle_run_persistence_builds_run_result_for_controller_path(tmp_path: Path) -> None:
    highscore_path = tmp_path / "highscore.json"
    highscore = Highscore()
    stats = SessionStats()
    controller = _FakeController()

    handle_run_persistence(
        highscore=highscore,
        highscore_json_path=str(highscore_path),
        stats=stats,
        session_controller=controller,
        active_player_id=17,
        score=410,
        elapsed_ms=8_250,
        coins_value_sum=19,
        won=True,
        bronze_count=2,
        silver_count=2,
        gold_count=1,
        diamond_count=1,
    )

    saved = load_highscore(str(highscore_path))

    assert stats.runs == 0
    assert len(controller.recorded_results) == 1
    assert controller.recorded_results[0] == RunResult(
        player_id=17,
        score=410,
        elapsed_ms=8_250,
        coins_value_sum=19,
        won=True,
        bronze_count=2,
        silver_count=2,
        gold_count=1,
        diamond_count=1,
    )
    assert saved.best_score == 410
    assert saved.max_coins_value == 19
    assert saved.best_time_ms == 8_250
