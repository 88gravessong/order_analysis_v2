from datetime import date

from metrics_core import classify_order_status, date_in_range, locate_columns, metric_rates, to_date


def test_classify_order_status_shared_rules():
    assert classify_order_status("Completed", "", None) == "completed"
    assert classify_order_status("已送达", "anything", None) == "delivered"
    assert classify_order_status("Refund requested", "", None) == "refund"
    assert classify_order_status("Canceled", "", "") == "cancel_before"
    assert classify_order_status("Canceled", "", "2025-07-01 10:00:00") == "cancel_after"
    assert classify_order_status("In transit", "", None) == "in_transit"
    assert classify_order_status("Awaiting shipment", "", None) is None


def test_date_parsing_and_range_supports_common_exports():
    assert to_date("2025年07月08日") == date(2025, 7, 8)
    assert to_date("20250708") == date(2025, 7, 8)
    assert to_date("08/07/2025") == date(2025, 7, 8)
    assert date_in_range("2025-07-08 12:30:00", date(2025, 7, 1), date(2025, 7, 31))
    assert not date_in_range("bad date", date(2025, 7, 1), date(2025, 7, 31))


def test_locate_columns_supports_province_aliases_and_cancellation_spelling():
    headers = [
        "Seller SKU",
        "Order Substatus",
        "Cancellation/Return Type",
        "Shipped Time",
        "Created Time",
        "State/Province",
    ]

    cols = locate_columns(headers, include_province=True)

    assert cols["seller_sku"] == 0
    assert cols["cancel_type"] == 2
    assert cols["province"] == 5


def test_metric_rates_rounds_and_keeps_sign_rate_definition():
    rates = metric_rates(
        {
            "total": 4,
            "completed": 1,
            "delivered": 1,
            "refund": 1,
            "cancel_before": 1,
        }
    )

    assert rates["sign_rate"] == 75
    assert rates["completed_rate"] == 25
    assert rates["cancel_before_rate"] == 25
