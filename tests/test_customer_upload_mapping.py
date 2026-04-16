from controllers.dashboard.customer_controller import (
    build_customer_import_payload,
    filter_field_definitions_by_runtime_columns,
    get_runtime_customer_load_attrs,
    serialize_model_for_runtime_insert,
)


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


def test_runtime_schema_filter_hides_fields_missing_from_customer_table():
    runtime_columns_by_target = {
        "customer": {"full_name", "primary_phone", "upload_batch", "status", "search_name", "search_nik"},
        "address": {"full_address", "address_type", "is_primary", "is_active", "raw_lat_lng"},
        "loan": {"is_current", "loan_number", "total_outstanding", "overdue_days", "platform_name"},
        "contact": {"contact_type", "contact_role", "name", "phone_number"},
        "import_row": {"upload_batch", "import_status", "import_error_flag", "raw_customer_name", "raw_phone", "raw_address", "raw_lat_lng", "raw_payload"},
    }

    visible_keys = {
        field["key"]
        for field in filter_field_definitions_by_runtime_columns(runtime_columns_by_target)
    }

    assert "full_name" in visible_keys
    assert "partner_name" not in visible_keys
    assert "birth_date" not in visible_keys


def test_runtime_insert_serializer_omits_customer_columns_missing_from_live_schema():
    result = build_customer_import_payload(
        row={"Nama": "Siti Aminah", "No HP": "08123456789", "Partner": "Partner A"},
        mapping={
            "full_name": "Nama",
            "primary_phone": "No HP",
            "partner_name": "Partner",
        },
        batch_code="UPLOAD_20260416_100000",
    )

    runtime_columns_by_target = {
        "customer": {"full_name", "primary_phone", "status", "upload_batch", "search_name"},
        "address": set(),
        "loan": set(),
        "contact": set(),
        "import_row": set(),
    }

    serialized = serialize_model_for_runtime_insert(
        result.customer,
        "customer",
        runtime_columns_by_target,
    )

    assert serialized["full_name"] == "Siti Aminah"
    assert serialized["primary_phone"] == "08123456789"
    assert "partner_name" not in serialized


def test_runtime_insert_serializer_backfills_required_legacy_customer_columns():
    result = build_customer_import_payload(
        row={
            "Nama": "IJUSRI PIRMATIA",
            "No HP": "82386031271",
            "Alamat": "Bukit Senang",
        },
        mapping={
            "full_name": "Nama",
            "primary_phone": "No HP",
            "full_address": "Alamat",
        },
        batch_code="UPLOAD_20260416_100000",
    )

    runtime_columns_by_target = {
        "customer": {
            "name",
            "address",
            "phone",
            "full_name",
            "primary_phone",
            "primary_address_summary",
            "status",
            "upload_batch",
            "search_name",
            "is_deleted",
        },
        "address": set(),
        "loan": set(),
        "contact": set(),
        "import_row": set(),
    }

    serialized = serialize_model_for_runtime_insert(
        result.customer,
        "customer",
        runtime_columns_by_target,
    )

    assert serialized["name"] == "IJUSRI PIRMATIA"
    assert serialized["address"] == "Bukit Senang"
    assert serialized["phone"] == "82386031271"
    assert serialized["is_deleted"] == 0


def test_runtime_insert_serializer_sets_created_at_when_column_exists():
    result = build_customer_import_payload(
        row={"Nama": "Siti Aminah"},
        mapping={"full_name": "Nama"},
        batch_code="UPLOAD_20260416_100000",
    )

    runtime_columns_by_target = {
        "customer": {"full_name", "status", "upload_batch", "search_name", "created_at"},
        "address": set(),
        "loan": set(),
        "contact": set(),
        "import_row": set(),
    }

    serialized = serialize_model_for_runtime_insert(
        result.customer,
        "customer",
        runtime_columns_by_target,
    )

    assert serialized["created_at"] is not None


def test_runtime_customer_load_attrs_hide_missing_columns():
    attrs = get_runtime_customer_load_attrs(
        {
            "customer": {"id", "full_name", "primary_phone", "status", "upload_batch"},
            "address": set(),
            "loan": set(),
            "contact": set(),
            "import_row": set(),
        }
    )

    attr_keys = {attr.key for attr in attrs}

    assert "full_name" in attr_keys
    assert "partner_name" not in attr_keys
