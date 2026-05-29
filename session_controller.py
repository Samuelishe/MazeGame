from __future__ import annotations

"""
session_controller.py — управление игроками и сохранением результатов забегов.

Содержит:
    - RoundMode — режим смены игроков между забегами;
    - RunResult — данные одного завершённого забега;
    - GameSessionController — контроллер текущей игровой сессии:
        * хранит список игроков;
        * знает текущего активного игрока;
        * управляет очередностью игроков;
        * обновляет SessionStats в памяти;
        * пишет агрегаты и историю забегов в SQLite.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict

from db_manager import PathType, init_db
from domain.player_models import PlayerProfile
from persistence.player_repository import (
    load_players,
    get_or_create_player,
    create_player,
    delete_player,
)
from persistence.run_repository import write_completed_run
from runtime.session_stats import SessionStats


class RoundMode(str, Enum):
    """
    Режим смены игроков между забегами.

    SINGLE:
        Одиночный режим. После забега активный игрок не меняется.
        Игрока можно сменить вручную через экран выбора игрока.

    ROTATE_QUEUE:
        Мультиплеер по очереди. После каждого забега активный игрок
        автоматически переключается на следующего в списке players.

    PICK_EACH_ROUND:
        Мультиплеер со свободным выбором. После каждого забега
        предполагается, что следующий игрок будет выбран вручную
        через отдельный экран (PlayerSelectState).
    """

    SINGLE = "single"
    ROTATE_QUEUE = "rotate_queue"
    PICK_EACH_ROUND = "pick_each_round"


@dataclass(frozen=True)
class RunResult:
    """
    Результат одного завершённого забега.

    player_id:
        Идентификатор игрока, к которому относится результат.
    score:
        Финальные очки, посчитанные по ScoreParams.
    elapsed_ms:
        Время забега в миллисекундах.
    coins_value_sum:
        Суммарная ценность монет (value), собранных за попытку.
    won:
        True, если забег завершился победой.
    *_count:
        Количество монет каждой редкости за этот забег.
    """

    player_id: int
    score: int
    elapsed_ms: int
    coins_value_sum: int
    won: bool
    bronze_count: int
    silver_count: int
    gold_count: int
    diamond_count: int


@dataclass
class GameSessionController:
    """
    Контроллер игровой сессии Maze Game.

    Отвечает за:
        - список игроков и текущего активного;
        - режим смены игроков (RoundMode);
        - сессионную статистику по каждому игроку (SessionStats);
        - сохранение результатов забегов в SQLite (runs + player_stats).

    Этот класс НЕ занимается логикой Pygame и отрисовкой — только данными.
    """

    db_path: PathType
    players: list[PlayerProfile]
    mode: RoundMode = RoundMode.SINGLE
    current_index: int = 0
    session_stats_by_player: Dict[int, SessionStats] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Гарантирует корректность состояния сразу после создания.

        - инициализирует БД (init_db);
        - если список игроков пуст, создаёт одного игрока по умолчанию;
        - создаёт SessionStats для каждого игрока, если их ещё нет;
        - нормализует current_index.
        """
        init_db(self.db_path)

        if not self.players:
            # защитный кейс: создаём игрока по умолчанию
            default_profile = get_or_create_player(self.db_path, "Игрок 1")
            self.players = [default_profile]

        # нормализуем индекс
        if self.current_index < 0 or self.current_index >= len(self.players):
            self.current_index = 0

        # создаём SessionStats для всех, у кого ещё нет
        for profile in self.players:
            self.session_stats_by_player.setdefault(profile.player_id, SessionStats())

    @classmethod
    def from_db(
        cls,
        db_path: PathType,
        *,
        mode: RoundMode = RoundMode.SINGLE,
        ensure_default_player: bool = True,
        default_player_name: str = "Игрок 1",
    ) -> "GameSessionController":
        """
        Фабричный метод: создаёт контроллер, загрузив игроков из БД.

        :param db_path: путь к SQLite-файлу.
        :param mode: режим смены игроков (по умолчанию — одиночный).
        :param ensure_default_player:
            Если True и в БД нет ни одного игрока, будет создан default_player_name.
        :param default_player_name:
            Имя игрока по умолчанию, если нужно создать первого.
        :return: готовый GameSessionController.
        """
        init_db(db_path)
        players = load_players(db_path)
        if ensure_default_player and not players:
            profile = get_or_create_player(db_path, default_player_name)
            players = [profile]

        return cls(
            db_path=db_path,
            players=players,
            mode=mode,
        )

    def set_mode(self, mode: RoundMode) -> None:
        """
        Устанавливает режим смены игроков.

        При смене режима индекс текущего игрока НЕ сбрасывается,
        чтобы игрок не «терялся» при переключении режимов.
        """
        self.mode = mode

    def advance_after_run(self) -> None:
        """
        Вызывается после каждого завершённого забега.

        В зависимости от режима может изменить активного игрока.

        SINGLE:
            Ничего не делает — всегда один активный игрок.
        ROTATE_QUEUE:
            Сдвигает current_index по кругу на следующего игрока.
        PICK_EACH_ROUND:
            Не трогает current_index — следующий игрок выбирается
            вручную на экранах меню.
        """
        if not self.players:
            return

        if self.mode == RoundMode.SINGLE:
            # Одиночный режим — активный игрок не меняется автоматически.
            return

        if self.mode == RoundMode.ROTATE_QUEUE:
            if len(self.players) > 1:
                self.current_index = (self.current_index + 1) % len(self.players)
            return

        if self.mode == RoundMode.PICK_EACH_ROUND:
            # В этом режиме выбор игрока происходит вручную в меню.
            return

    def create_player(self, name: str) -> PlayerProfile:
        """
        Создаёт нового игрока с указанным именем, добавляет его в контроллер
        и инициализирует для него сессионную статистику.

        :param name: имя игрока (уникальное, не пустое).
        :return: созданный профиль игрока.
        :raises ValueError: если имя пустое или такой игрок уже существует.
        """
        profile = create_player(self.db_path, name)
        self.players.append(profile)
        self.session_stats_by_player[profile.player_id] = SessionStats()
        return profile

    def delete_player_from_session(self, player_id: int) -> None:
        """
        Удаляет игрока из БД и из текущей сессии.

        Поведение:
            - нельзя удалить последнего оставшегося игрока;
            - current_index сдвигается так, чтобы всегда указывать
              на валидного игрока;
            - сессионная статистика игрока удаляется из памяти.

        :param player_id: идентификатор игрока для удаления.
        :raises ValueError: если игрок не найден или это последний игрок.
        """
        if len(self.players) <= 1:
            raise ValueError("Нельзя удалить последнего игрока.")

        # Находим индекс игрока в локальном списке
        delete_index: int | None = None
        for idx, profile in enumerate(self.players):
            if profile.player_id == player_id:
                delete_index = idx
                break

        if delete_index is None:
            raise ValueError(f"Игрок с id={player_id} не найден в контроллере.")

        # Сначала удаляем из БД (каскадно удалятся player_stats и runs)
        delete_player(self.db_path, player_id)

        # Удаляем из локального списка и сессионной статистики
        self.players.pop(delete_index)
        self.session_stats_by_player.pop(player_id, None)

        # Нормализуем current_index
        if not self.players:
            # Теоретически не должно случиться из-за проверки выше,
            # но на всякий случай.
            default_profile = get_or_create_player(self.db_path, "Игрок 1")
            self.players = [default_profile]
            self.current_index = 0
            self.session_stats_by_player.setdefault(default_profile.player_id, SessionStats())
            return

        if delete_index < self.current_index:
            self.current_index -= 1
        elif delete_index == self.current_index:
            # Если удалили текущего — сдвигаем индекс к предыдущему
            # или оставляем 0, если удалили первый.
            if self.current_index >= len(self.players):
                self.current_index = len(self.players) - 1

    def current_player(self) -> PlayerProfile:
        """
        Возвращает текущего активного игрока.
        """
        return self.players[self.current_index]

    def next_player_auto(self) -> PlayerProfile:
        """
        Переключает активного игрока по кругу (используется в режиме ROTATE).

        :return: новый текущий PlayerProfile.
        """
        if not self.players:
            raise RuntimeError("Список игроков пуст в GameSessionController.")
        self.current_index = (self.current_index + 1) % len(self.players)
        return self.current_player()

    def choose_player(self, player_id: int) -> PlayerProfile:
        """
        Делает указанного игрока текущим.

        Используется в ручном режиме (MANUAL) из меню выбора игрока.

        :param player_id: идентификатор игрока.
        :return: выбранный PlayerProfile.
        :raises ValueError: если игрока с таким id нет в списке контроллера.
        """
        for idx, profile in enumerate(self.players):
            if profile.player_id == player_id:
                self.current_index = idx
                return profile
        raise ValueError(f"Игрок с id={player_id} не найден в контроллере.")

    def configure_rotation_players(self, player_ids: list[int]) -> None:
        """
        Настраивает список игроков для мультиплеера по очереди.

        В текущей сессии будут участвовать только игроки из player_ids
        (в указанном порядке, без дубликатов). Остальные игроки остаются
        в БД, но не участвуют в данной игровой сессии, пока конфигурация
        не будет изменена или сессия не будет пересоздана.

        :param player_ids: список идентификаторов игроков в нужном порядке.
        :raises ValueError: если список пуст или в нём нет ни одного
            существующего игрока.
        """
        if not player_ids:
            raise ValueError("Список игроков для мультиплеера не может быть пустым.")

        # Убираем дубликаты, сохраняем порядок.
        unique_ids: list[int] = []
        seen: set[int] = set()
        for pid in player_ids:
            if pid not in seen:
                unique_ids.append(pid)
                seen.add(pid)

        # Строим новый список профилей в указанном порядке.
        id_to_profile: dict[int, PlayerProfile] = {p.player_id: p for p in self.players}
        new_players: list[PlayerProfile] = []
        for pid in unique_ids:
            profile = id_to_profile.get(pid)
            if profile is not None:
                new_players.append(profile)

        if not new_players:
            raise ValueError("Не найдено ни одного игрока для мультиплеера.")

        self.players = new_players

        valid_ids = {p.player_id for p in self.players}

        # Чистим сессионную статистику от неиспользуемых игроков.
        self.session_stats_by_player = {
            pid: stats
            for pid, stats in self.session_stats_by_player.items()
            if pid in valid_ids
        }

        # Инициализируем SessionStats для тех, у кого ещё нет.
        for profile in self.players:
            self.session_stats_by_player.setdefault(profile.player_id, SessionStats())

        # Начинаем очередь с первого игрока.
        self.current_index = 0


    def get_session_stats_for(self, player_id: int) -> SessionStats:
        """
        Возвращает сессионную статистику для указанного игрока.

        Если статистики ещё не было, создаётся новая запись.
        """
        stats = self.session_stats_by_player.get(player_id)
        if stats is None:
            stats = SessionStats()
            self.session_stats_by_player[player_id] = stats
        return stats

    def record_run(self, result: RunResult) -> None:
        """
        Регистрирует завершённый забег:

        - обновляет SessionStats для соответствующего игрока;
        - делегирует persistence write path в отдельный repository boundary.

        Эта функция не занимается пересчётом highscore.json — только SQLite.
        """
        # 1) обновляем сессионную статистику в памяти
        stats = self.get_session_stats_for(result.player_id)
        stats.add_result(
            won=result.won,
            coins_value_sum=result.coins_value_sum,
            elapsed_ms=result.elapsed_ms,
            score=result.score,
            bronze_count=result.bronze_count,
            silver_count=result.silver_count,
            gold_count=result.gold_count,
            diamond_count=result.diamond_count,
        )

        # 2) делегируем raw SQL write path в persistence boundary
        write_completed_run(self.db_path, result)
