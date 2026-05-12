from typing import List
from .schemas import CanonicalPurchaseOrder, CanonicalInvoice

class EDIValidator:
    @staticmethod
    def validate_purchase_order(po: CanonicalPurchaseOrder) -> List[str]:
        errors: List[str] = []
        if not po.po_number or po.po_number == "UNKNOWN":
            errors.append("Mandatory BEG03 PO number missing")
        if not po.po_date:
            errors.append("Mandatory BEG05 PO date missing")
        if not po.line_items:
            errors.append("At least one PO1 line item is mandatory")
        else:
            for idx, item in enumerate(po.line_items, 1):
                if item.quantity <= 0:
                    errors.append(f"Line {idx}: Quantity must be positive, got {item.quantity}")
                if item.unit_price <= 0:
                    errors.append(f"Line {idx}: Unit price must be positive, got {item.unit_price}")
        return errors

    @staticmethod
    def validate_invoice(inv: CanonicalInvoice) -> List[str]:
        errors: List[str] = []
        if not inv.invoice_number or inv.invoice_number == "UNKNOWN":
            errors.append("Mandatory BIG02 Invoice number missing")
        if not inv.invoice_date:
            errors.append("Mandatory BIG01 Invoice date missing")
        if inv.total_amount < 0:
            errors.append("Invoice total cannot be negative")
        return errors
