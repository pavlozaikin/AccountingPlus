from __future__ import annotations

from datetime import date, timedelta
from typing import Any, List, Optional, Sequence

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

    RNOKPP_LENGTH = 10
    RNOKPP_BASE_DATE = date(1899, 12, 31)

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

    def _has_value(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, str):
            return bool(value.strip())
        return True

    def _normalize_rnokpp(self, value: Any) -> Optional[str]:
        if not self._has_value(value):
            return None
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        if len(digits) != self.RNOKPP_LENGTH:
            return None
        return digits

    def _rnokpp_ninth_digit(self, rnokpp_value: Any) -> Optional[int]:
        digits = self._normalize_rnokpp(rnokpp_value)
        if not digits:
            return None
        try:
            return int(digits[8])
        except (ValueError, IndexError):
            return None

    def _rnokpp_birth_date_days(self, rnokpp_value: Any) -> Optional[int]:
        digits = self._normalize_rnokpp(rnokpp_value)
        if not digits:
            return None
        try:
            days = int(digits[:5])
        except ValueError:
            return None
        return days

    def _all_fields_present(self, fact: Fact, fields: Sequence[str]) -> bool:
        return all(self._has_value(fact.get(field)) for field in fields)

    def _format_date(self, value: Any) -> Optional[str]:
        parsed = self._parse_date(value)
        if parsed:
            return parsed.strftime("%d.%m.%Y")
        if isinstance(value, str) and value:
            return value
        return None

    @Rule(PersonData(birth_date=MATCH.birth_date))
    def recommend_below_service_age(self, birth_date: Any) -> None:  # type: ignore[override]
        age = self._calculate_age(birth_date)
        if age is None or age >= 16:
            return
        self._recommendations.append("Особа не досягла віку перебування на військовому обліку")

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
            f"{account_category} {first_name} {last_name} має бути виключений з військового обліку у звʼязку з досягненням граничного віку"
        )

    @Rule(
        PersonData(
            account_category=MATCH.account_category,
            mobil_order_date=MATCH.mobil_order_date,
        )
    )
    def recommend_prizovnik_with_mobil_order(
        self, account_category: str, mobil_order_date: Any
    ) -> None:  # type: ignore[override]
        if account_category != "призовник":
            return
        if not self._has_value(mobil_order_date):
            return
        self._recommendations.append(
            "Призовник не може мати мобілізаційне розпорядження. Скоригуйте категорію обліку"
        )

    @Rule(
        PersonData(
            account_category=MATCH.account_category,
            mil_rank=MATCH.mil_rank,
        )
    )
    def recommend_prizovnik_has_rank(self, account_category: str, mil_rank: Optional[str]) -> None:  # type: ignore[override]
        if account_category != "призовник":
            return
        if not self._has_value(mil_rank):
            return
        self._recommendations.append("Військові звання призовникам не присвоюються")

    @Rule(
        PersonData(
            account_category=MATCH.account_category,
            vos_code=MATCH.vos_code,
        )
    )
    def recommend_prizovnik_has_vos(self, account_category: str, vos_code: Optional[str]) -> None:  # type: ignore[override]
        if account_category != "призовник":
            return
        if not self._has_value(vos_code):
            return
        self._recommendations.append("Призовники не можуть мати військово-облікову спеціальність")

    @Rule(
        PersonData(
            account_category=MATCH.account_category,
            mil_rank=MATCH.mil_rank,
        )
    )
    def recommend_missing_rank_for_obliged(
        self, account_category: str, mil_rank: Optional[str]
    ) -> None:  # type: ignore[override]
        if account_category != "військовозобовʼязаний":
            return
        if self._has_value(mil_rank):
            return
        self._recommendations.append(
            "Переконайтесь, що військове звання (принаймні рекрут) відсутнє у військово-обліковому документі"
        )

    @Rule(
        PersonData(
            account_category=MATCH.account_category,
            mil_rank=MATCH.mil_rank,
        )
    )
    def recommend_missing_rank_for_reservist(
        self, account_category: str, mil_rank: Optional[str]
    ) -> None:  # type: ignore[override]
        if account_category != "резервіст":
            return
        if self._has_value(mil_rank):
            return
        self._recommendations.append(
            "Перевірте військово-обліковий документ на відсутність записів про присвоєння військового звання"
        )

    @Rule(PersonData(email=MATCH.email))
    def recommend_unsafe_email(self, email: str) -> None:  # type: ignore[override]
        if not self._has_value(email):
            return
        domain = email.lower().strip().split("@")[-1]
        banned_domains = {
            "mail.ru",
            "list.ru",
            "bk.ru",
            "inbox.ru",
            "yandex.ru",
            "yandex.com",
            "ya.ru",
            "rambler.ru",
        }
        if domain in banned_domains:
            self._recommendations.append(
                "Використовується email-сервіс держави-агресора. Негайно змініть email!"
            )

    @Rule(
        PersonData(
            gender=MATCH.gender,
            rnokpp=MATCH.rnokpp,
            first_name=MATCH.first_name,
            last_name=MATCH.last_name,
        )
    )
    def recommend_rnokpp_gender_parity_male(
        self, gender: str, rnokpp: Any, first_name: str, last_name: str
    ) -> None:  # type: ignore[override]
        if gender != "male":
            return
        ninth_digit = self._rnokpp_ninth_digit(rnokpp)
        if ninth_digit is None or ninth_digit % 2 != 0:
            return
        self._recommendations.append(
            f"{first_name} {last_name} має \"жіночий\" РНОКПП. Усуньте помилку"
        )

    @Rule(
        PersonData(
            gender=MATCH.gender,
            rnokpp=MATCH.rnokpp,
            first_name=MATCH.first_name,
            last_name=MATCH.last_name,
        )
    )
    def recommend_rnokpp_gender_parity_female(
        self, gender: str, rnokpp: Any, first_name: str, last_name: str
    ) -> None:  # type: ignore[override]
        if gender != "female":
            return
        ninth_digit = self._rnokpp_ninth_digit(rnokpp)
        if ninth_digit is None or ninth_digit % 2 == 0:
            return
        self._recommendations.append(
            f"{first_name} {last_name} має \"чоловічий\" РНОКПП. Усуньте помилку"
        )

    @Rule(PersonData(rnokpp=MATCH.rnokpp, birth_date=MATCH.birth_date))
    def recommend_rnokpp_birthdate_mismatch(self, rnokpp: Any, birth_date: Any) -> None:  # type: ignore[override]
        birth = self._parse_date(birth_date)
        if not birth:
            return
        days_from_rnokpp = self._rnokpp_birth_date_days(rnokpp)
        if days_from_rnokpp is None:
            return
        expected_days = (birth - self.RNOKPP_BASE_DATE).days
        if days_from_rnokpp == expected_days:
            return
        self._recommendations.append("У РНОКПП виявлено ймовірну помилку у перших 5 цифрах")

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

    @Rule(PersonData(deferral_until=MATCH.deferral_until))
    def recommend_expired_deferral(self, deferral_until: Any) -> None:  # type: ignore[override]
        expiry = self._parse_date(deferral_until)
        if not expiry:
            return
        if date.today() <= expiry:
            return
        self._recommendations.append("Строк дії відстрочки сплив. Оновіть про неї дані")

    @Rule(PersonData(booking_until=MATCH.booking_until))
    def recommend_expired_booking(self, booking_until: Any) -> None:  # type: ignore[override]
        expiry = self._parse_date(booking_until)
        if not expiry:
            return
        if date.today() <= expiry:
            return
        self._recommendations.append("Строк дії бронювання сплив. Оновіть про нього дані")

    @Rule(
        PersonData(
            account_category=MATCH.account_category,
            position_name=MATCH.position_name,
            appoint_order_date=MATCH.appoint_order_date,
        )
    )
    def recommend_missing_position_for_appointment(
        self, account_category: str, position_name: Optional[str], appoint_order_date: Any
    ) -> None:  # type: ignore[override]
        if not self._has_value(appoint_order_date):
            return
        if self._has_value(position_name):
            return
        self._recommendations.append(f"Вкажіть на яку посаду призначено {account_category}")

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

    @Rule(
        PersonData(
            birth_date=MATCH.birth_date,
            mobil_order_date=MATCH.mobil_order_date,
        )
    )
    def recommend_mobil_order_underage(
        self, birth_date: Any, mobil_order_date: Any
    ) -> None:  # type: ignore[override]
        birth = self._parse_date(birth_date)
        mobil = self._parse_date(mobil_order_date)
        if not birth or not mobil:
            return
        eighteenth = self._add_years(birth, 18)
        if not eighteenth:
            return
        if mobil < eighteenth:
            self._recommendations.append(
                "Мобілізаційне розпорядження не може бути видано неповнолітній особі"
            )

    @Rule(
        PersonData(
            mobil_order_date=MATCH.mobil_order_date,
            unit_number=MATCH.unit_number,
        )
    )
    def recommend_missing_unit_number(
        self, mobil_order_date: Any, unit_number: Optional[str]
    ) -> None:  # type: ignore[override]
        if not self._has_value(mobil_order_date):
            return
        if self._has_value(unit_number):
            return
        self._recommendations.append(
            "Не вказано номер військової частини у мобілізаційному розпорядженні"
        )

    @Rule(
        PersonData(
            mobil_order_date=MATCH.mobil_order_date,
            unit_number=MATCH.unit_number,
        )
    )
    def recommend_missing_mobil_order_date(
        self, mobil_order_date: Any, unit_number: Optional[str]
    ) -> None:  # type: ignore[override]
        if self._has_value(mobil_order_date):
            return
        if not self._has_value(unit_number):
            return
        self._recommendations.append(
            "Не вказано дату видачі мобілізаційного розпорядження"
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

    @Rule(AS.person_fact << PersonData())
    def recommend_missing_edrpvr(self, person_fact: Fact) -> None:  # type: ignore[override]
        if self._has_value(person_fact.get("edrpvr_number")):
            return
        self._recommendations.append("Додайте номер у ЄДРПВР")

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
