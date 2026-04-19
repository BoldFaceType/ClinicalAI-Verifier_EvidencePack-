from __future__ import annotations

import json
from pathlib import Path

from evidence_packer.models.fhir_models import EvidenceExcerpt
from evidence_packer.strategy.evidence_mapper import EvidencePlan


def generate_appeal_packet(
    *,
    output_dir: Path,
    claim_response_path: Path,
    outcome: str,
    denial_code: str,
    denial_text: str,
    evidence_plan: EvidencePlan,
    excerpts: list[EvidenceExcerpt],
    correlation_id: str,
    profile: str,
    extraction_mode: str,
) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    packet_path = output_dir / "appeal_packet.pdf"
    manifest_path = output_dir / "packet.json"
    required_documents = getattr(
        evidence_plan, "required_documents", getattr(evidence_plan, "evidence_types", [])
    )
    manifest = {
        "contract_version": "evidence.packet.v1",
        "correlation_id": correlation_id,
        "profile": profile,
        "claim_response_file": str(claim_response_path),
        "outcome": outcome,
        "denial_code": denial_code,
        "denial_text": denial_text,
        "strategy_category": evidence_plan.category,
        "required_documents": list(required_documents),
        "evidence_excerpts": [excerpt.__dict__ for excerpt in excerpts],
        "extraction_mode": extraction_mode,
        "extraction_engine": "governed_v1",
        "appeal_ready": bool(excerpts),
        "packet_pdf": str(packet_path),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    lines = [
        f"Outcome: {outcome}",
        f"Denial Code: {denial_code}",
        f"Denial Text: {denial_text}",
        f"Strategy Category: {evidence_plan.category}",
        "Required Documents:",
        *[f"- {item}" for item in manifest["required_documents"]],
        "Evidence Excerpts:",
        *[f"- {excerpt.source} ({excerpt.confidence:.2f}): {excerpt.excerpt}" for excerpt in excerpts],
    ]
    manifest["pdf_renderer"] = _write_pdf(packet_path, title="Appeal Packet", lines=lines)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def _write_pdf(path: Path, *, title: str, lines: list[str]) -> str:
    if _write_reportlab_pdf(path, title=title, lines=lines):
        return "reportlab"
    _write_simple_pdf(path, title=title, lines=lines)
    return "builtin_minimal"


def _write_reportlab_pdf(path: Path, *, title: str, lines: list[str]) -> bool:
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except ImportError:
        return False

    pdf = canvas.Canvas(str(path), pagesize=letter, pageCompression=0, invariant=1)
    width, height = letter
    y = height - 72
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(72, y, title)
    y -= 24
    pdf.setFont("Helvetica", 11)
    for line in lines:
        if y < 72:
            pdf.showPage()
            y = height - 72
            pdf.setFont("Helvetica", 11)
        pdf.drawString(72, y, line[:140])
        y -= 16
    pdf.save()
    return True


def _write_simple_pdf(path: Path, *, title: str, lines: list[str]) -> None:
    text_lines = [title, "", *lines]
    content = (
        "BT /F1 12 Tf 72 760 Td 14 TL "
        + " ".join(f"({_escape_pdf_text(line)}) Tj T*" for line in text_lines)
        + " ET"
    )
    content_bytes = content.encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >> endobj\n",
        f"4 0 obj << /Length {len(content_bytes)} >> stream\n".encode("ascii")
        + content_bytes
        + b"\nendstream endobj\n",
        b"5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
    ]
    header = b"%PDF-1.4\n"
    output = bytearray(header)
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)
    xref_offset = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    output.extend(
        (
            f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n"
        ).encode("ascii")
    )
    path.write_bytes(output)


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
