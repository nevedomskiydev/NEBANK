"""Tests for the expense parser — covers concrete TZ §5–§8 examples."""
from datetime import date

from app.services.parser import parse_bank_sms, parse_message
from app.services.parser.numbers import find_amount, words_to_number

TODAY = date(2026, 6, 30)


def amounts(text, base="USD"):
    return [(e.title, e.amount, e.currency, e.kind, e.occurred_at) for e in parse_message(text, base, TODAY)]


def test_multi_entry():
    res = amounts("кофе 200, такси 350, кино 500", "RUB")
    assert [r[1] for r in res] == [200.0, 350.0, 500.0]
    assert [r[0] for r in res] == ["кофе", "такси", "кино"]
    assert all(r[2] == "RUB" for r in res)


def test_words_fraction_crypto():
    res = amounts("ноль точка ноль ноль ноль шесть биткоинов")
    assert len(res) == 1
    assert abs(res[0][1] - 0.0006) < 1e-9
    assert res[0][2] == "BTC"


def test_words_to_number_variants():
    assert words_to_number("две тысячи пятьсот") == 2500.0
    assert words_to_number("twelve") == 12.0
    assert words_to_number("ноль точка ноль ноль ноль шесть") == 0.0006


def test_thousands_and_decimal_separators():
    assert find_amount("1 200,50")[0] == 1200.5
    assert find_amount("1,200.50")[0] == 1200.5
    assert find_amount("2k")[0] == 2000.0


def test_dates_day_first():
    # 4.07 -> 4 July (day first, not 7 April); amount must not be eaten by the date
    res = parse_message("кино 500 4.07", "RUB", TODAY)[0]
    assert res.amount == 500.0
    assert (res.occurred_at.day, res.occurred_at.month) == (4, 7)
    res2 = parse_message("такси 100 вчера", "RUB", TODAY)[0]
    assert res2.amount == 100.0
    assert res2.occurred_at == date(2026, 6, 29)
    res3 = parse_message("обед 300 15 января", "RUB", TODAY)[0]
    assert res3.amount == 300.0
    assert (res3.occurred_at.day, res3.occurred_at.month) == (15, 1)


def test_income_detection():
    res = amounts("зарплата 5000 usd вчера", "RUB")[0]
    assert res[3] == "income"
    assert res[2] == "USD"
    assert res[4] == date(2026, 6, 29)


def test_keeps_item_name():
    res = parse_message("Онлайн Игра 200", "RUB", TODAY)[0]
    assert res.title == "Онлайн Игра"
    assert res.amount == 200.0


def test_decimal_comma_not_split():
    res = amounts("такси 1 200,50 руб", "RUB")
    assert len(res) == 1
    assert res[0][1] == 1200.5


def test_sms_parse_and_dedup_hash():
    a = parse_bank_sms("Покупка 1234.56 RUB в Пятёрочка", "RUB")
    b = parse_bank_sms("Покупка 1234.56 RUB в Пятёрочка", "RUB")
    assert a is not None and a.amount == 1234.56 and a.kind == "expense"
    assert a.dedup_hash == b.dedup_hash  # same SMS -> same hash (dedup)
    assert parse_bank_sms("just a normal message") is None


def test_english_capture():
    res = amounts("coffee 4, taxi 7", "USD")
    assert [r[1] for r in res] == [4.0, 7.0]
    assert [r[0] for r in res] == ["coffee", "taxi"]
