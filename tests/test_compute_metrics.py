from datetime import date
from io import BytesIO

from compute_logic import compute_metrics
from compute_province_metrics import compute_metrics_streams


def csv_stream(rows):
    text = "\n".join(",".join(str(cell) for cell in row) for row in rows)
    return BytesIO(text.encode("utf-8-sig"))


def test_compute_metrics_filters_date_and_groups_by_sku():
    stream = csv_stream(
        [
            ["Seller SKU", "Order Substatus", "Cancelation/Return Type", "Shipped Time", "Created Time"],
            ["desc", "desc", "desc", "desc", "desc"],
            ["SKU-A", "Completed", "", "", "2025-07-08"],
            ["SKU-A", "Canceled", "", "", "2025-07-09"],
            ["SKU-B", "Delivered", "", "", "2025-08-01"],
        ]
    )

    _, stats = compute_metrics([stream], date(2025, 7, 1), date(2025, 7, 31))

    assert stats["SKU-A"]["total"] == 2
    assert stats["SKU-A"]["completed"] == 1
    assert stats["SKU-A"]["cancel_before"] == 1
    assert "SKU-B" not in stats


def test_compute_province_metrics_groups_by_sku_and_province():
    stream = csv_stream(
        [
            [
                "Seller SKU",
                "Province",
                "Order Substatus",
                "Cancelation/Return Type",
                "Shipped Time",
                "Created Time",
            ],
            ["desc", "desc", "desc", "desc", "desc", "desc"],
            ["SKU-A", "MX-CMX", "Delivered", "", "", "2025-07-08"],
            ["SKU-A", "MX-JAL", "Refund requested", "", "", "2025-07-09"],
            ["SKU-A", "MX-CMX", "Canceled", "", "2025-07-10", "2025-07-10"],
        ]
    )

    stats, sku_totals = compute_metrics_streams([stream], date(2025, 7, 1), date(2025, 7, 31))

    assert sku_totals["SKU-A"] == 3
    assert stats["SKU-A"]["MX-CMX"]["total"] == 2
    assert stats["SKU-A"]["MX-CMX"]["delivered"] == 1
    assert stats["SKU-A"]["MX-CMX"]["cancel_after"] == 1
    assert stats["SKU-A"]["MX-JAL"]["refund"] == 1
