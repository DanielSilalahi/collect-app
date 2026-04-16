from services.customer_import import build_customer_import_payload


def test_import_row_preserves_raw_lat_lng_and_snapshot_fields():
    row = {
        "Nama": "Siti Aminah",
        "No HP": "08123456789",
        "Alamat": "Jl. Mawar No. 7",
        "Loan Number": "P2P-009",
        "OS": "1500000",
        "DPD": "18",
        "Lat&Lng": "-6.2,106.8",
    }

    result = build_customer_import_payload(
        row=row,
        mapping={
            "full_name": "Nama",
            "primary_phone": "No HP",
            "full_address": "Alamat",
            "loan_number": "Loan Number",
            "total_outstanding": "OS",
            "overdue_days": "DPD",
            "raw_lat_lng": "Lat&Lng",
        },
        batch_code="UPLOAD_20260416_100000",
    )

    assert result.customer.full_name == "Siti Aminah"
    assert result.customer.primary_phone == "08123456789"
    assert result.loan.loan_number == "P2P-009"
    assert str(result.loan.total_outstanding) == "1500000"
    assert result.loan.overdue_days == 18
    assert result.address.raw_lat_lng == "-6.2,106.8"
    assert result.import_row.raw_payload["Lat&Lng"] == "-6.2,106.8"
