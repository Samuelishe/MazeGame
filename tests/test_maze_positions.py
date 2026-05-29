from gameplay.maze_positions import inner_cell_from_border


def test_inner_cell_from_border_left() -> None:
    assert inner_cell_from_border((5, 0), "left") == (5, 1)


def test_inner_cell_from_border_right() -> None:
    assert inner_cell_from_border((5, 10), "right") == (5, 9)


def test_inner_cell_from_border_top() -> None:
    assert inner_cell_from_border((0, 7), "top") == (1, 7)


def test_inner_cell_from_border_bottom() -> None:
    assert inner_cell_from_border((10, 7), "bottom") == (9, 7)


def test_inner_cell_from_border_invalid_side_raises_value_error() -> None:
    try:
        inner_cell_from_border((1, 1), "diagonal")
    except ValueError:
        return
    assert False, "Expected ValueError for unsupported border side"
