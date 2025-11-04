from __future__ import annotations

from typing import List

try:
    from experta import MATCH, Fact, KnowledgeEngine, Rule
except ImportError as exc:  # pragma: no cover - defensive guard for missing dependency
    raise ImportError(
        "Experta library is required for recommendation support. Install it via 'pip install experta'."
    ) from exc


class PersonData(Fact):
    """Fact that stores data about a person for the expert system."""
    pass


class PersonRecommendationEngine(KnowledgeEngine):
    """Small wrapper around Experta KnowledgeEngine for person suggestions."""

    def __init__(self) -> None:
        super().__init__()
        self._recommendations: List[str] = []

    @Rule(PersonData(account_category="призовник"))
    def recommend_registration(self) -> None:
        self._recommendations.append(
            "Переконайтеся, що призовник має приписне посвідчення та актуальні контакти ТЦК." 
        )

    @Rule(PersonData(account_category="військовозобовʼязаний"))
    def recommend_reserve(self) -> None:
        self._recommendations.append(
            "Уточніть наявність чинного військово-облікового документа та мобілізаційного розпорядження."
        )

    @Rule(PersonData(account_category="резервіст"))
    def recommend_reservist(self) -> None:
        self._recommendations.append(
            "Перевірте своєчасність оновлення даних у Реєстрі військовозобовʼязаних та план навчань."
        )

    @Rule(PersonData(deferral_until=MATCH.deferral_until))
    def recommend_deferral(self, deferral_until: str) -> None:  # type: ignore[override]
        self._recommendations.append(
            f"Підтвердіть дійсність відстрочки до {deferral_until} та наявність підтверджувальних документів."
        )

    @Rule(PersonData(booking_until=MATCH.booking_until))
    def recommend_booking(self, booking_until: str) -> None:  # type: ignore[override]
        self._recommendations.append(
            f"Нагадуйте відповідальному працівнику про завершення бронювання {booking_until}."
        )

    def get_recommendations(self) -> List[str]:
        return self._recommendations
