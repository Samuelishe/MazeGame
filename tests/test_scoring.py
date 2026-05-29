from gameplay.scoring import ScoreParams, compute_score


def test_compute_score_win_with_coin_and_diamond_bonus() -> None:
    params = ScoreParams()

    score = compute_score(
        coins_value_sum=10,
        elapsed_ms=2000,
        won=True,
        diamond_count=2,
        params=params,
    )

    assert score == 1874


def test_compute_score_loss_without_time_penalty() -> None:
    params = ScoreParams(apply_time_on_loss=False)

    score = compute_score(
        coins_value_sum=10,
        elapsed_ms=999_999,
        won=False,
        diamond_count=1,
        params=params,
    )

    assert score == 245


def test_compute_score_never_below_zero() -> None:
    params = ScoreParams(
        coin_k=0,
        time_penalty_per_sec=10.0,
        win_bonus=0,
        win_multiplier=1.0,
        loss_multiplier=1.0,
        diamond_bonus=0,
        apply_time_on_loss=True,
    )

    score = compute_score(
        coins_value_sum=0,
        elapsed_ms=5_000,
        won=False,
        diamond_count=0,
        params=params,
    )

    assert score == 0
