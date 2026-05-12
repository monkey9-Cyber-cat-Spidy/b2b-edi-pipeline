from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .parser import EDIX12Parser
from .validator import EDIValidator
from .schemas import ParseResult

app = FastAPI(
    title="B2B EDI Processing Pipeline",
    version="1.0.0",
    description="High-speed ANSI X12 EDI stream parser, canonical schema validator, and 997 Functional Acknowledgment generator"
)

parser = EDIX12Parser()

class RawEDIRequest(BaseModel):
    raw_edi: str

@app.get("/health")
def health():
    return {"status": "UP", "service": "b2b-edi-pipeline"}

@app.post("/api/edi/parse", response_model=ParseResult)
def parse_edi_transaction(request: RawEDIRequest):
    try:
        trans_type, parsed_dict, ack_997 = parser.parse(request.raw_edi)
        ctrl = parsed_dict.get("interchange", {}).get("control_number", "000000001")

        val_errors = []
        if trans_type == "850_PURCHASE_ORDER":
            from .schemas import CanonicalPurchaseOrder
            po = CanonicalPurchaseOrder(**parsed_dict)
            val_errors = EDIValidator.validate_purchase_order(po)
        elif trans_type == "810_INVOICE":
            from .schemas import CanonicalInvoice
            inv = CanonicalInvoice(**parsed_dict)
            val_errors = EDIValidator.validate_invoice(inv)

        return ParseResult(
            success=(len(val_errors) == 0),
            transaction_type=trans_type,
            control_number=ctrl,
            data=parsed_dict,
            acknowledgment_997=ack_997,
            validation_errors=val_errors
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
