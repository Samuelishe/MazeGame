from __future__ import annotations

"""In-memory per-session aggregate state for the current process lifetime."""

from dataclasses import dataclass


@dataclass
class SessionStats:
    """
    Счётчики текущей игровой сессии (пока процесс не закрыт):

    - runs: количество попыток;
    - wins / deaths: победы и поражения;
    - total_score: суммарные очки;
    - total_time_ms: суммарное время;
    - total_coins: суммарная ценность монет;
    - *_total: общий счётчик монет по редкостям.

    Эта статистика живёт только в памяти и не связана напрямую с БД.
    """

    runs: int = 0
    wins: int = 0
    deaths: int = 0
    total_score: int = 0
    total_time_ms: int = 0
    total_coins: int = 0

    bronze_total: int = 0
    silver_total: int = 0
    gold_total: int = 0
    diamond_total: int = 0

    def add_result(
        self,
        *,
        won: bool,
        coins_value_sum: int,
        elapsed_ms: int,
        score: int,
        bronze_count: int,
        silver_count: int,
        gold_count: int,
        diamond_count: int,
    ) -> None:
        """
        Обновляет агрегированные значения по результату одного забега.

        :param won: True, если забег завершился победой.
        :param coins_value_sum: сумма номиналов монет за попытку.
        :param elapsed_ms: длительность забега в миллисекундах.
        :param score: финальный счёт.
        :param bronze_count: количество бронзовых монет за забег.
        :param silver_count: количество серебряных монет за забег.
        :param gold_count: количество золотых монет за забег.
        :param diamond_count: количество бриллиантов за забег.
        """
        self.runs += 1
        self.total_coins += coins_value_sum
        self.total_time_ms += elapsed_ms
        self.total_score += score

        self.bronze_total += bronze_count
        self.silver_total += silver_count
        self.gold_total += gold_count
        self.diamond_total += diamond_count

        if won:
            self.wins += 1
        else:
            self.deaths += 1

    def summary_line(self) -> str:
        """
        Возвращает краткую сводку по сессии одной строкой для HUD/оверлея.

        Пример:
            "Сессия: попыток 5 • побед 2 • смертей 3 • очки 1234 • "
            "ценность монет 17 • ср. время 1:12.345 • 🥉7 • 🥈6 • 🥇3 • 💎1"
        """
        avg_time_ms = self.total_time_ms // max(1, self.runs)
        base = (
            f"Сессия: попыток {self.runs} • побед {self.wins} • смертей {self.deaths} • "
            f"очки {self.total_score} • ценность монет {self.total_coins} • "
            f"ср. время {self._format_time(avg_time_ms)}"
        )
        by_types = (
            f" • 🥉{self.bronze_total} • 🥈{self.silver_total} • "
            f"🥇{self.gold_total} • 💎{self.diamond_total}"
        )
        return base + by_types

    @staticmethod
    def _format_time(ms: int) -> str:
        """
        Локальная версия форматирования времени:
        М:SS.мс, например 1:23.456
        """
        seconds, msec = divmod(ms, 1000)
        minutes, sec = divmod(seconds, 60)
        return f"{minutes}:{sec:02d}.{msec:03d}"
