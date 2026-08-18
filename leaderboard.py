from __future__ import annotations
import json
from datetime import datetime
import config
class Leaderboard:
    def __init__(self) -> None:
        config.DATA_DIR.mkdir(exist_ok=True)
        self.scores = self._load()

    def _load(self) -> list[dict]:
        if not config.SCORES_FILE.exists():
            return []
        try:
            data = json.loads(config.SCORES_FILE.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [row for row in data if isinstance(row, dict)]
        except Exception as exc:
            print(f"Leaderboard file invalid, starting fresh: {exc}")
        return []

    def add(self, name: str, score: int, mode: str) -> None:
        self.scores.append(
            {
                "name": (name or "PLAYER")[:12],
                "score": int(score),
                "mode": mode,
                "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
        )
        self.scores.sort(key=lambda item: item.get("score", 0), reverse=True)
        self.scores = self.scores[: config.LEADERBOARD_LIMIT]
        try:
            config.SCORES_FILE.write_text(json.dumps(self.scores, indent=2), encoding="utf-8")
        except Exception as exc:
            print(f"Could not save leaderboard: {exc}")

    def qualifies(self, score: int) -> bool:
        return len(self.scores) < config.LEADERBOARD_LIMIT or score > min(row.get("score", 0) for row in self.scores)

    def export_pdf(self) -> str:
        lines = ["FRUIT FURY  |  HALL OF BLADES", "Top 100 local scores", ""]
        if not self.scores:
            lines.append("No scores recorded yet.")
        else:
            for rank, row in enumerate(self.scores, start=1):
                name = str(row.get("name", "PLAYER"))[:12]
                score = int(row.get("score", 0))
                mode = str(row.get("mode", "Classic"))[:18]
                date = str(row.get("date", ""))[:16]
                lines.append(f"{rank:>3}.  {name:<12}  {score:>7}  {mode:<18}  {date}")

        page_height = 792
        page_width = 612
        rows_per_page = 38
        pages = [lines[index : index + rows_per_page] for index in range(0, len(lines), rows_per_page)] or [[]]
        objects: list[bytes] = []

        def add_object(content: bytes) -> int:
            objects.append(content)
            return len(objects)

        catalog_id = add_object(b"")
        pages_id = add_object(b"")
        font_id = add_object(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")
        page_ids: list[int] = []
        for page_number, page_lines in enumerate(pages, start=1):
            commands = [b"BT", b"/F1 15 Tf", b"72 742 Td"]
            for line_number, line in enumerate(page_lines):
                safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1", "replace")
                if line_number == 0:
                    commands.append(b"0.18 0.05 0.12 rg")
                elif line_number == 1:
                    commands.append(b"0.45 0.08 0.24 rg")
                else:
                    commands.append(b"0.10 0.10 0.14 rg")
                commands.append(b"(" + safe_line + b") Tj")
                commands.append(b"0 -18 Td")
            footer = f"Page {page_number} of {len(pages)}".encode("ascii")
            commands.extend([b"0.35 0.08 0.22 rg", b"0 -12 Td", b"(" + footer + b") Tj", b"ET"])
            stream = b"\n".join(commands)
            content_id = add_object(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
            page_ids.append(add_object(
                b"<< /Type /Page /Parent " + str(pages_id).encode("ascii") + b" 0 R /MediaBox [0 0 "
                + str(page_width).encode("ascii") + b" " + str(page_height).encode("ascii")
                + b"] /Resources << /Font << /F1 " + str(font_id).encode("ascii")
                + b" 0 R >> >> /Contents " + str(content_id).encode("ascii") + b" 0 R >>"
            ))

        objects[catalog_id - 1] = b"<< /Type /Catalog /Pages " + str(pages_id).encode("ascii") + b" 0 R >>"
        kids = b" ".join(str(page_id).encode("ascii") + b" 0 R" for page_id in page_ids)
        objects[pages_id - 1] = b"<< /Type /Pages /Kids [" + kids + b"] /Count " + str(len(page_ids)).encode("ascii") + b" >>"

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for object_id, content in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{object_id} 0 obj\n".encode("ascii"))
            pdf.extend(content)
            pdf.extend(b"\nendobj\n")
        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode("ascii"))
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010} 00000 n \n".encode("ascii"))
        pdf.extend(f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("ascii"))
        config.LEADERBOARD_PDF_FILE.write_bytes(pdf)
        return str(config.LEADERBOARD_PDF_FILE)
