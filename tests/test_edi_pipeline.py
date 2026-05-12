import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.parser import EDIX12Parser
from app.validator import EDIValidator
from app.schemas import CanonicalPurchaseOrder, EDILineItem, InterchangeControl

client = TestClient(app)

SAMPLE_850_EDI = (
    "ISA*00*          *00*          *ZZ*WALMART        *ZZ*SUPPLIER       *261017*1030*U*00401*000000101*0*P*>~"
    "GS*PO*WALMART*SUPPLIER*20261017*1030*101*X*004010~"
    "ST*850*0001~"
    "BEG*00*NE*PO-98472**20261017~"
    "N1*BY*WALMART STORE 1042~"
    "N1*SE*GLOBAL LOGISTICS PARTNER~"
    "PO1*1*100*EA*15.50**VP*WIDGET-PRO-A~"
    "PO1*2*50*EA*22.00**VP*SENSOR-MOD-B~"
    "CTT*2~"
    "SE*8*0001~"
    "GE*1*101~"
    "IEA*1*000000101~"
)

SAMPLE_810_EDI = (
    "ISA*00*          *00*          *ZZ*SUPPLIER       *ZZ*WALMART        *261017*1100*U*00401*000000102*0*P*>~"
    "GS*IN*SUPPLIER*WALMART*20261017*1100*102*X*004010~"
    "ST*810*0001~"
    "BIG*20261017*INV-55410**PO-98472~"
    "IT1*1*100*EA*15.50**VP*WIDGET-PRO-A~"
    "TDS*155000~"
    "SE*5*0001~"
    "GE*1*102~"
    "IEA*1*000000102~"
)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "UP"

def test_parse_850_purchase_order():
    parser = EDIX12Parser()
    trans_type, data, ack_997 = parser.parse(SAMPLE_850_EDI)

    assert trans_type == "850_PURCHASE_ORDER"
    assert data["po_number"] == "PO-98472"
    assert data["buyer_name"] == "WALMART STORE 1042"
    assert len(data["line_items"]) == 2
    assert data["line_items"][0]["quantity"] == 100.0
    assert data["line_items"][0]["unit_price"] == 15.50
    assert data["total_amount"] == 2650.0  # (100 * 15.5) + (50 * 22.0) = 1550 + 1100 = 2650
    assert "AK5*A~" in ack_997

def test_parse_810_invoice():
    parser = EDIX12Parser()
    trans_type, data, ack_997 = parser.parse(SAMPLE_810_EDI)

    assert trans_type == "810_INVOICE"
    assert data["invoice_number"] == "INV-55410"
    assert data["po_reference"] == "PO-98472"
    assert len(data["line_items"]) == 1
    assert data["line_items"][0]["sku"] == "WIDGET-PRO-A"
    assert "AK5*A~" in ack_997

def test_validator_detects_invalid_line_item():
    invalid_po = CanonicalPurchaseOrder(
        po_number="PO-INVALID",
        po_date="20261017",
        total_amount=0.0,
        line_items=[
            EDILineItem(line_number="1", quantity=-5.0, unit="EA", unit_price=-10.0, sku="BAD-SKU")
        ],
        interchange=InterchangeControl(
            sender_id="A", receiver_id="B", control_number="1", date="261017", time="1200"
        )
    )
    errors = EDIValidator.validate_purchase_order(invalid_po)
    assert len(errors) == 2
    assert any("Quantity must be positive" in e for e in errors)
    assert any("Unit price must be positive" in e for e in errors)

def test_fastapi_parse_endpoint():
    response = client.post("/api/edi/parse", json={"raw_edi": SAMPLE_850_EDI})
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["transaction_type"] == "850_PURCHASE_ORDER"
    assert res_data["data"]["po_number"] == "PO-98472"
    assert len(res_data["validation_errors"]) == 0
