from typing import Dict, Any, List, Tuple
from .schemas import (
    CanonicalPurchaseOrder,
    CanonicalInvoice,
    EDILineItem,
    InterchangeControl
)

class EDIX12Parser:
    def __init__(self, element_delimiter: str = "*", segment_terminator: str = "~"):
        self.element_delimiter = element_delimiter
        self.segment_terminator = segment_terminator

    def tokenize_segments(self, raw_edi: str) -> List[List[str]]:
        raw_edi = raw_edi.strip().replace("\r", "").replace("\n", "")
        raw_segments = [s.strip() for s in raw_edi.split(self.segment_terminator) if s.strip()]
        tokenized = []
        for seg in raw_segments:
            elements = seg.split(self.element_delimiter)
            tokenized.append(elements)
        return tokenized

    def parse(self, raw_edi: str) -> Tuple[str, Dict[str, Any], str]:
        segments = self.tokenize_segments(raw_edi)
        if not segments:
            raise ValueError("Empty or invalid EDI document")

        # Extract Interchange Header (ISA)
        isa = segments[0]
        if isa[0] != "ISA" or len(isa) < 16:
            raise ValueError("Invalid ISA header segment")

        sender_id = isa[6].strip()
        receiver_id = isa[8].strip()
        control_num = isa[13].strip()
        date_str = isa[9].strip()
        time_str = isa[10].strip()

        interchange = InterchangeControl(
            sender_id=sender_id,
            receiver_id=receiver_id,
            control_number=control_num,
            date=date_str,
            time=time_str
        )

        # Detect Transaction Set (ST)
        st_segment = next((s for s in segments if s[0] == "ST"), None)
        if not st_segment or len(st_segment) < 3:
            raise ValueError("ST (Transaction Set Header) missing or invalid")

        trans_type = st_segment[1]
        st_control = st_segment[2]

        if trans_type == "850":
            po_data = self._parse_850(segments, interchange)
            ack_997 = self.generate_997_ack(interchange, st_control, "A", len(segments))
            return "850_PURCHASE_ORDER", po_data.model_dump(), ack_997
        elif trans_type == "810":
            inv_data = self._parse_810(segments, interchange)
            ack_997 = self.generate_997_ack(interchange, st_control, "A", len(segments))
            return "810_INVOICE", inv_data.model_dump(), ack_997
        else:
            ack_997 = self.generate_997_ack(interchange, st_control, "R", len(segments))
            return f"UNSUPPORTED_{trans_type}", {"raw_segments": len(segments)}, ack_997

    def _parse_850(self, segments: List[List[str]], interchange: InterchangeControl) -> CanonicalPurchaseOrder:
        po_number = "UNKNOWN"
        po_date = ""
        buyer_name = None
        seller_name = None
        line_items: List[EDILineItem] = []
        total_amount = 0.0

        for seg in segments:
            tag = seg[0]
            if tag == "BEG" and len(seg) >= 4:
                po_number = seg[3]
                po_date = seg[5] if len(seg) > 5 else ""
            elif tag == "N1" and len(seg) >= 3:
                entity_role = seg[1]
                if entity_role == "BY":
                    buyer_name = seg[2]
                elif entity_role == "SE":
                    seller_name = seg[2]
            elif tag == "PO1" and len(seg) >= 5:
                line_no = seg[1]
                qty = float(seg[2]) if seg[2] else 0.0
                unit = seg[3] if len(seg) > 3 else "EA"
                price = float(seg[4]) if len(seg) > 4 else 0.0
                sku = seg[7] if len(seg) > 7 else (seg[6] if len(seg) > 6 else f"ITEM-{line_no}")
                total_amount += (qty * price)
                line_items.append(EDILineItem(
                    line_number=line_no,
                    quantity=qty,
                    unit=unit,
                    unit_price=price,
                    sku=sku
                ))

        return CanonicalPurchaseOrder(
            po_number=po_number,
            po_date=po_date,
            buyer_name=buyer_name,
            seller_name=seller_name,
            total_amount=round(total_amount, 2),
            line_items=line_items,
            interchange=interchange
        )

    def _parse_810(self, segments: List[List[str]], interchange: InterchangeControl) -> CanonicalInvoice:
        invoice_number = "UNKNOWN"
        invoice_date = ""
        po_reference = None
        total_amount = 0.0
        line_items: List[EDILineItem] = []

        for seg in segments:
            tag = seg[0]
            if tag == "BIG" and len(seg) >= 4:
                invoice_date = seg[1]
                invoice_number = seg[2]
                po_reference = seg[4] if len(seg) > 4 else None
            elif tag == "IT1" and len(seg) >= 5:
                line_no = seg[1]
                qty = float(seg[2]) if seg[2] else 0.0
                unit = seg[3] if len(seg) > 3 else "EA"
                price = float(seg[4]) if len(seg) > 4 else 0.0
                sku = seg[7] if len(seg) > 7 else f"SKU-{line_no}"
                total_amount += (qty * price)
                line_items.append(EDILineItem(
                    line_number=line_no,
                    quantity=qty,
                    unit=unit,
                    unit_price=price,
                    sku=sku
                ))
            elif tag == "TDS" and len(seg) >= 2:
                # TDS expresses amount in cents usually or direct dollar value
                try:
                    tds_val = float(seg[1]) / 100.0 if len(seg[1]) > 4 else float(seg[1])
                    if total_amount == 0.0:
                        total_amount = tds_val
                except ValueError:
                    pass

        return CanonicalInvoice(
            invoice_number=invoice_number,
            invoice_date=invoice_date,
            po_reference=po_reference,
            total_amount=round(total_amount, 2),
            line_items=line_items,
            interchange=interchange
        )

    def generate_997_ack(self, interchange: InterchangeControl, st_control: str, ack_code: str, segment_count: int) -> str:
        """
        Generates ANSI X12 997 Functional Acknowledgment
        AK1: Functional Group Response
        AK2: Transaction Set Response Header
        AK5: Transaction Set Response Trailer (A = Accepted, R = Rejected)
        AK9: Functional Group Response Trailer
        """
        d = self.element_delimiter
        t = self.segment_terminator
        return (
            f"ISA{d}00{d}          {d}00{d}          {d}ZZ{d}{interchange.receiver_id:<15}{d}ZZ{d}{interchange.sender_id:<15}{d}261017{d}1200{d}U{d}00401{d}999000001{d}0{d}P{d}>{t}\n"
            f"GS{d}FA{d}{interchange.receiver_id.strip()}{d}{interchange.sender_id.strip()}{d}20261017{d}1200{d}1{d}X{d}004010{t}\n"
            f"ST{d}997{d}0001{t}\n"
            f"AK1{d}PO{d}1{t}\n"
            f"AK2{d}850{d}{st_control}{t}\n"
            f"AK5{d}{ack_code}{t}\n"
            f"AK9{d}{ack_code}{d}1{d}1{d}1{t}\n"
            f"SE{d}6{d}0001{t}\n"
            f"GE{d}1{d}1{t}\n"
            f"IEA{d}1{d}999000001{t}"
        )
