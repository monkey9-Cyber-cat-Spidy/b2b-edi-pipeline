# B2B EDI Processing Pipeline

> Enterprise ANSI X12 EDI stream parser, canonical schema validator, and automated 997 Functional Acknowledgment generator.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-brightgreen.svg)](https://fastapi.tiangolo.com)
[![Pytest](https://img.shields.io/badge/Pytest-Passing-green.svg)](https://pytest.org)

---

## Architectural Overview

The **B2B EDI Processing Pipeline** is built for enterprise supply chain integration (retailers, manufacturers, and logistics networks). It ingests legacy ANSI ASC X12 electronic data interchange streams and transforms them into strictly validated modern JSON / Pydantic models for ERP systems.

```
[External EDI Partner (AS2/SFTP)]
                 │
                 ▼ (Raw ANSI X12 Stream: 850 PO / 810 Invoice)
     [EDIX12Parser Tokenizer]
     ├── ISA/IEA & GS/GE Envelope Extraction
     └── ST/SE Transaction Segment Parsing
                 │
                 ├───> [EDIValidator] ──> [Canonical Pydantic V2 Schema]
                 │                                │
                 │                                ▼
                 │                       [ERP / Cloud Database]
                 │
                 └───> [997 Functional Acknowledgment Generator]
                                                  │
                                                  ▼
                                 [Return ANSI X12 997 FA to Partner]
```

---

## Core Capabilities

1. **Multi-Transaction Support**:
   * **ANSI X12 850**: Purchase Order parsing (buyer/seller entities, PO line items, unit prices, quantity multipliers).
   * **ANSI X12 810**: Commercial Invoice parsing (terms, line-level billing, total gross calculations).
2. **Automated 997 Generation**:
   * Generates standard ASC X12 997 Functional Acknowledgments (AK1, AK2, AK5, AK9) signaling batch receipt or rejection status.
3. **Semantic Validation**:
   * Validates control numbers, envelope checksums, line item counts, and positive monetary quantities.

---

## Quick Start & Installation

```bash
# Clone the repository
git clone https://github.com/monkey9-Cyber-cat-Spidy/b2b-edi-pipeline.git
cd b2b-edi-pipeline

# Install dependencies
pip install -r requirements.txt

# Run pytest suite
pytest -v

# Run FastAPI server
uvicorn app.main:app --reload --port 8000
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status |
| `POST` | `/api/edi/parse` | Parse raw EDI X12 stream into canonical JSON + generate 997 Ack |

---

## Author

**Kuncham Venkata Satya Manikanta**
* Portfolio: [aiengineer.kunchamvenkatasatyamanikanta.online](https://aiengineer.kunchamvenkatasatyamanikanta.online/)
* GitHub: [@monkey9-Cyber-cat-Spidy](https://github.com/monkey9-Cyber-cat-Spidy)
* LinkedIn: [kuncham-venkata-satya-manikanta](https://www.linkedin.com/in/kuncham-venkata-satya-manikanta-9715a4321/)
