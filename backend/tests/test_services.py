from app.services.categorization import suggest_category
from app.services.receipt_extractor import ReceiptData, serialize_items


def test_smart_category_uses_vendor_and_description():
    assert suggest_category("GitHub Software", "team subscription") == "Software"
    assert suggest_category("Airport Hotel", "business trip") == "Travel"
    assert suggest_category("Unknown Vendor") == "Other"


def test_receipt_data_and_line_item_serialization():
    result = ReceiptData(vendor="Cafe", total=12.5, line_items=[{"name": "Lunch", "price": 12.5}])
    assert result.total == 12.5
    assert serialize_items(result.line_items) == '[{"name":"Lunch","price":12.5}]'
