from typing import List, Optional
from pydantic import BaseModel, Field

class EDILineItem(BaseModel):
    line_number: str
    quantity: float
    unit: str = "EA"
    unit_price: float
    sku: str
    description: Optional[str] = None

class InterchangeControl(BaseModel):
    sender_id: str
    receiver_id: str
    control_number: str
    date: str
    time: str

class CanonicalPurchaseOrder(BaseModel):
    po_number: str
    po_date: str
    buyer_name: Optional[str] = None
    buyer_code: Optional[str] = None
    seller_name: Optional[str] = None
    seller_code: Optional[str] = None
    total_amount: float
    currency: str = "USD"
    line_items: List[EDILineItem] = Field(default_factory=list)
    interchange: InterchangeControl

class CanonicalInvoice(BaseModel):
    invoice_number: str
    invoice_date: str
    po_reference: Optional[str] = None
    total_amount: float
    currency: str = "USD"
    line_items: List[EDILineItem] = Field(default_factory=list)
    interchange: InterchangeControl

class ParseResult(BaseModel):
    success: bool = True
    transaction_type: str
    control_number: str
    data: dict
    acknowledgment_997: str
    validation_errors: List[str] = Field(default_factory=list)
