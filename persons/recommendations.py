from __future__ import annotations

from datetime import date, timedelta
from typing import Any, List, Optional

try:
    from experta import AS, MATCH, Fact, KnowledgeEngine, Rule
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

    def _parse_date(self, value: Any) -> Optional[date]:
        if isinstance(value, date):
            return value
        if isinstance(value, str) and value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                return None
        return None

    def _calculate_age(self, birth_date_value: Any) -> Optional[int]:
        birth = self._parse_date(birth_date_value)
        if not birth:
            return None
        today = date.today()
        if birth > today:
            return None
        years = today.year - birth.year
        if (today.month, today.day) < (birth.month, birth.day):
            years -= 1
        return years

    def _days_until_deadline(self, base_date_value: Any, offset: int) -> Optional[int]:
        deadline = self._calculate_deadline(base_date_value, offset)
        if not deadline:
            return None
        return (deadline - date.today()).days

    def _calculate_deadline(self, base_date_value: Any, offset: int) -> Optional[date]:
        base_date = self._parse_date(base_date_value)
        if not base_date:
            return None
        return base_date + timedelta(days=offset)

    def _years_since(self, date_value: Any) -> Optional[int]:
        parsed = self._parse_date(date_value)
        if not parsed:
            return None
        today = date.today()
        if parsed > today:
            return 0
        years = today.year - parsed.year
        if (today.month, today.day) < (parsed.month, parsed.day):
            years -= 1
        return years

    def _add_years(self, date_value: Any, years: int) -> Optional[date]:
        base = self._parse_date(date_value)
        if not base:
            return None
        try:
            return base.replace(year=base.year + years)
        except ValueError:
            # Handle leap day by falling back to February 28 of the target year.
            return base.replace(month=2, day=28, year=base.year + years)

    def _format_date(self, value: Any) -> Optional[str]:
        parsed = self._parse_date(value)
        if parsed:
            return parsed.strftime("%d.%m.%Y")
        if isinstance(value, str) and value:
            return value
        return None

    @Rule(
        PersonData(
            account_category=MATCH.account_category,
            first_name=MATCH.first_name,
            last_name=MATCH.last_name,
            birth_date=MATCH.birth_date,
        )
    )
    def recommend_underage_category(
        self, account_category: str, first_name: str, last_name: str, birth_date: Any
    ) -> None:  # type: ignore[override]
        if account_category not in {"призовник", "військовозобовʼязаний"}:
            return
        age = self._calculate_age(birth_date)
        if age is None or age >= 18:
            return
        self._recommendations.append("Перевірте визначення категорії обліку неповнолітнього")

    @Rule(
        PersonData(
            account_category=MATCH.account_category,
            first_name=MATCH.first_name,
            last_name=MATCH.last_name,
            birth_date=MATCH.birth_date,
        )
    )
    def recommend_age_limit(
        self, account_category: str, first_name: str, last_name: str, birth_date: Any
    ) -> None:  # type: ignore[override]
        if account_category not in {"військовозобовʼязаний", "резервіст"}:
            return
        age = self._calculate_age(birth_date)
        if age is None or age <= 60:
            return
        self._recommendations.append(
            f"{first_name} {last_name} має бути виключений з військового обліку у звʼязку з досягненням граничного віку"
        )

    @Rule(
        PersonData(
            first_name=MATCH.first_name,
            last_name=MATCH.last_name,
            deferral_until=MATCH.deferral_until,
            deferral_reason=MATCH.deferral_reason,
            booking_until=MATCH.booking_until,
        )
    )
    def recommend_deferral_booking(
        self,
        first_name: str,
        last_name: str,
        deferral_until: Any,
        deferral_reason: str,
        booking_until: Any,
    ) -> None:  # type: ignore[override]
        if not deferral_until or not booking_until:
            return
        deferral_text = self._format_date(deferral_until) or str(deferral_until)
        self._recommendations.append(
            f"{first_name} {last_name} може не включатися до списку на бронювання до {deferral_text}, адже має відстрочку ({deferral_reason})"
        )

    @Rule(
        AS.person_fact
        << PersonData(
            first_name=MATCH.first_name,
            last_name=MATCH.last_name,
            appoint_order_date=MATCH.appoint_order_date,
        )
    )
    def recommend_missing_appoint_notification(
        self, person_fact: Fact, first_name: str, last_name: str, appoint_order_date: Any
    ) -> None:  # type: ignore[override]
        if not appoint_order_date:
            return
        notif_appoint_date = person_fact.get("notif_appoint_date")
        if notif_appoint_date:
            return
        deadline = self._calculate_deadline(appoint_order_date, 7)
        if not deadline:
            return
        days_left = self._days_until_deadline(appoint_order_date, 7)
        if days_left is None:
            return
        if days_left > 0:
            self._recommendations.append(
                f"Не подано повідомлення до ТЦК та СП про призначення {first_name} {last_name} на посаду. Залишилось {days_left} днів"
            )
            return
        deadline_text = self._format_date(deadline) or str(deadline)
        self._recommendations.append(
            f"Повідомлення про призначення {first_name} {last_name} на посаду необхідно було подати до {deadline_text}"
        )

    @Rule(
        AS.person_fact
        << PersonData(
            first_name=MATCH.first_name,
            last_name=MATCH.last_name,
            dismiss_order_date=MATCH.dismiss_order_date,
        )
    )
    def recommend_missing_dismiss_notification(
        self, person_fact: Fact, first_name: str, last_name: str, dismiss_order_date: Any
    ) -> None:  # type: ignore[override]
        if not dismiss_order_date:
            return
        notif_dismiss_date = person_fact.get("notif_dismiss_date")
        if notif_dismiss_date:
            return
        deadline = self._calculate_deadline(dismiss_order_date, 7)
        if not deadline:
            return
        days_left = self._days_until_deadline(dismiss_order_date, 7)
        if days_left is None:
            return
        if days_left > 0:
            self._recommendations.append(
                f"Не подано повідомлення до ТЦК та СП про звільнення {first_name} {last_name}. Залишилось {days_left} днів."
            )
            return
        deadline_text = self._format_date(deadline) or str(deadline)
        self._recommendations.append(
            f"Повідомлення про звільнення {first_name} {last_name} з посади необхідно було подати до {deadline_text}"
        )

    @Rule(PersonData(birth_date=MATCH.birth_date))
    def recommend_birth_date_check(self, birth_date: Any) -> None:  # type: ignore[override]
        age = self._calculate_age(birth_date)
        if age is None or age <= 125:
            return
        self._recommendations.append("Переконайтеся, що дата народження вказана правильно")

    @Rule(
        PersonData(
            address_registered=MATCH.address_registered,
            address_actual=MATCH.address_actual,
        )
    )
    def recommend_single_address(self, address_registered: str, address_actual: str) -> None:  # type: ignore[override]
        if not address_registered or not address_actual:
            return
        if address_registered != address_actual:
            return
        self._recommendations.append("Вказуйте лише задеклароване місце проживання")

    @Rule(
        PersonData(
            address_registered=MATCH.address_registered,
            address_actual=MATCH.address_actual,
        )
    )
    def recommend_dual_address(self, address_registered: str, address_actual: str) -> None:  # type: ignore[override]
        if not address_registered or not address_actual:
            return
        if address_registered == address_actual:
            return
        self._recommendations.append("Необхідно зазначити задеклароване та фактичне місце проживання")

    @Rule(PersonData(edrpvr_number=MATCH.edrpvr_number))
    def recommend_missing_edrpvr(self, edrpvr_number: Optional[str]) -> None:  # type: ignore[override]
        if edrpvr_number:
            return
        self._recommendations.append("Вкажіть номер в ЄДРПВР")

    @Rule(
        PersonData(
            first_name=MATCH.first_name,
            last_name=MATCH.last_name,
            passport_issued_date=MATCH.passport_issued_date,
        )
    )
    def recommend_passport_update(
        self,
        first_name: str,
        last_name: str,
        passport_issued_date: Any,
    ) -> None:  # type: ignore[override]
        years = self._years_since(passport_issued_date)
        if years is None or years <= 10:
            return
        expiry_date = self._add_years(passport_issued_date, 10)
        expiry_text = self._format_date(expiry_date) if expiry_date else None
        if expiry_text:
            expiry_text = f"{expiry_text}"
        else:
            expiry_text = "[невідомо]"
        self._recommendations.append(
            f"Оновіть дані про паспорт (ID-картку) термін дії якого сплив {expiry_text}"
        )

    def get_recommendations(self) -> List[str]:
        return self._recommendations
