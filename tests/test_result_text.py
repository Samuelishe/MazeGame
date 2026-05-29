from gameplay.result_text import (
    build_attempt_info,
    build_coin_types_line,
    build_end_menu_subtitle,
    build_highscore_line,
)


def test_build_attempt_info_for_win() -> None:
    assert (
        build_attempt_info(
            won=True,
            time_str="1:23.456",
            coins_value_sum=17,
            score=1234,
        )
        == "Время: 1:23.456 • ценность монет 17 • Очки: 1234"
    )


def test_build_coin_types_line() -> None:
    assert build_coin_types_line(
        bronze_count=1,
        silver_count=2,
        gold_count=3,
        diamond_count=4,
    ) == "🥉1 • 🥈2 • 🥇3 • 💎4"


def test_build_end_menu_subtitle() -> None:
    subtitle = build_end_menu_subtitle(
        attempt_info="attempt",
        types_line="types",
        high_line="high",
        session_info="session",
    )

    assert subtitle == (
        "attempt\n"
        "types\n"
        "high\n"
        "session\n"
        "Enter/Space/R — заново • N — другой уровень • Esc — выход"
    )


def test_build_attempt_info_for_loss() -> None:
    assert (
        build_attempt_info(
            won=False,
            time_str="0:12.345",
            coins_value_sum=5,
            score=99,
        )
        == "Ты держался 0:12.345 • ценность монет 5 • Очки: 99"
    )


def test_build_highscore_line() -> None:
    assert build_highscore_line(
        best_score=100,
        best_time_str="0:10.000",
        max_coins_value=20,
        bronze_max=1,
        silver_max=2,
        gold_max=3,
        diamond_max=4,
    ) == "Рекорд: очки 100 • время 0:10.000 • ценность монет 20  🥉1 • 🥈2 • 🥇3 • 💎4"
