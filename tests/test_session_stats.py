from runtime.session_stats import SessionStats


def test_add_result_updates_win_counters_score_and_coins() -> None:
    stats = SessionStats()

    stats.add_result(
        won=True,
        coins_value_sum=17,
        elapsed_ms=12_345,
        score=500,
        bronze_count=1,
        silver_count=2,
        gold_count=3,
        diamond_count=4,
    )

    assert stats.runs == 1
    assert stats.wins == 1
    assert stats.deaths == 0
    assert stats.total_score == 500
    assert stats.total_time_ms == 12_345
    assert stats.total_coins == 17
    assert stats.bronze_total == 1
    assert stats.silver_total == 2
    assert stats.gold_total == 3
    assert stats.diamond_total == 4


def test_add_result_updates_loss_counters_accumulatively() -> None:
    stats = SessionStats()

    stats.add_result(
        won=True,
        coins_value_sum=10,
        elapsed_ms=4_000,
        score=100,
        bronze_count=1,
        silver_count=0,
        gold_count=0,
        diamond_count=0,
    )
    stats.add_result(
        won=False,
        coins_value_sum=5,
        elapsed_ms=6_000,
        score=50,
        bronze_count=0,
        silver_count=1,
        gold_count=0,
        diamond_count=0,
    )

    assert stats.runs == 2
    assert stats.wins == 1
    assert stats.deaths == 1
    assert stats.total_score == 150
    assert stats.total_time_ms == 10_000
    assert stats.total_coins == 15
    assert stats.bronze_total == 1
    assert stats.silver_total == 1


def test_summary_line_uses_average_time_and_all_aggregates() -> None:
    stats = SessionStats(
        runs=2,
        wins=1,
        deaths=1,
        total_score=150,
        total_time_ms=10_000,
        total_coins=15,
        bronze_total=1,
        silver_total=1,
        gold_total=0,
        diamond_total=0,
    )

    assert stats.summary_line() == (
        "Сессия: попыток 2 • побед 1 • смертей 1 • "
        "очки 150 • ценность монет 15 • ср. время 0:05.000"
        " • 🥉1 • 🥈1 • 🥇0 • 💎0"
    )
