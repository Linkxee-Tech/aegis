"""
PDF report export utilities for Aegis.

The exporter intentionally avoids external PDF dependencies so the feature can
work in the current environment without a new packaging step. It generates a
simple, standards-compliant PDF using the built-in Helvetica font.
"""

from __future__ import annotations

import datetime as dt
import textwrap
from typing import Any


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 48
TOP_MARGIN = 744
LINE_HEIGHT = 14
LINES_PER_PAGE = 42


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _slugify(text: str) -> str:
    cleaned = []
    for char in text.lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    return "".join(cleaned).strip("-") or "report"


def _wrap_paragraph(text: str, width: int = 88) -> list[str]:
    if not text:
        return [""]
    lines: list[str] = []
    for paragraph in text.splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(
            textwrap.wrap(
                paragraph,
                width=width,
                break_long_words=False,
                break_on_hyphens=False,
                replace_whitespace=False,
            )
        )
    return lines or [""]


def _section(title: str) -> list[str]:
    return ["", title.upper(), ""]


def _report_lines(report: dict[str, Any]) -> list[str]:
    lines: list[str] = [
        f"Incident Report: {report.get('title', 'Untitled')}",
        f"Report ID: {report.get('id', 'N/A')}",
        f"Incident ID: {report.get('incidentId', 'N/A')}",
        f"Generated At: {report.get('generatedAt', dt.datetime.now(dt.timezone.utc).isoformat())}",
        f"Status: {str(report.get('status', 'draft')).title()}",
        f"Downtime: {report.get('downtimeMinutes', 0)} minutes",
    ]
    if report.get("costImpactEstimate"):
        lines.append(f"Cost Impact: {report['costImpactEstimate']}")

    lines += _section("Executive Summary")
    lines.extend(_wrap_paragraph(report.get("summary", "")))

    lines += _section("Root Cause Analysis")
    lines.extend(_wrap_paragraph(report.get("rootCauseAnalysis", "")))

    lines += _section("Actions Taken")
    for index, action in enumerate(report.get("actionsTaken", []), start=1):
        lines.extend(_wrap_paragraph(f"{index}. {action}"))

    markdown_report = report.get("markdownReport")
    if markdown_report:
        lines += _section("Markdown Report")
        lines.extend(_wrap_paragraph(markdown_report, width=90))

    return lines


def _split_pages(lines: list[str]) -> list[list[str]]:
    pages: list[list[str]] = []
    for start in range(0, len(lines), LINES_PER_PAGE):
        pages.append(lines[start : start + LINES_PER_PAGE])
    return pages or [[""]]


def _build_content_stream(lines: list[str]) -> bytes:
    commands = [
        "BT",
        "/F1 11 Tf",
        f"{LEFT_MARGIN} {TOP_MARGIN} Td",
        f"{LINE_HEIGHT} TL",
    ]
    for index, line in enumerate(lines):
        escaped = _escape_pdf_text(line)
        if index == 0:
            commands.append(f"({escaped}) Tj")
        else:
            commands.append(f"T* ({escaped}) Tj")
    commands.append("ET")
    stream = "\n".join(commands).encode("utf-8")
    return stream


def _render_pdf_objects(report: dict[str, Any]) -> list[bytes]:
    pages = _split_pages(_report_lines(report))
    page_count = len(pages)

    objects: list[bytes] = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        ("<< /Type /Pages /Kids [" + " ".join(f"{5 + i * 2} 0 R" for i in range(page_count)) + f"] /Count {page_count} >>").encode(
            "utf-8"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    for index, lines in enumerate(pages):
        content_object = 4 + index * 2
        page_object = 5 + index * 2
        content_stream = _build_content_stream(lines)
        objects.append(
            f"<< /Length {len(content_stream)} >>\nstream\n".encode("utf-8") + content_stream + b"\nendstream"
        )
        objects.append(
            (
                "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
                f"/Resources << /Font << /F1 3 0 R >> >> /Contents {content_object} 0 R >>"
            ).encode("utf-8")
        )

    return objects


def build_report_pdf(report: dict[str, Any]) -> bytes:
    """
    Build a very small PDF document for an incident report.

    The output is intentionally plain text with multiple pages rather than a
    layout-heavy document, because the submission needs a reliable export path
    more than a flashy one.
    """
    objects = _render_pdf_objects(report)

    output = bytearray()
    output.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    offsets: list[int] = [0]
    for object_number, payload in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{object_number} 0 obj\n".encode("utf-8"))
        output.extend(payload)
        output.extend(b"\nendobj\n")

    xref_position = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n".encode("utf-8"))
    output.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode("utf-8"))
    output.extend(
        (
            "trailer\n"
            f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
            "startxref\n"
            f"{xref_position}\n"
            "%%EOF\n"
        ).encode("utf-8")
    )
    return bytes(output)


def build_report_filename(report: dict[str, Any]) -> str:
    title = _slugify(report.get("title", "report"))
    report_id = _slugify(str(report.get("id", "report")))
    return f"{report_id}-{title}.pdf"
