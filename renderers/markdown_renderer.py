import re
from dataclasses import dataclass
from renderers.font_manager import FontManager


@dataclass
class TextRun:
    text: str
    bold: bool = False
    italic: bool = False


class MarkdownRenderer:
    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.*)$")
    UL_PATTERN = re.compile(r"^[-*+]\s+(.*)$")
    OL_PATTERN = re.compile(r"^(\d+)[.)]\s+(.*)$")
    HR_PATTERN = re.compile(r"^(?:[-*_]\s*){3,}$")

    # Matches ***bold italic***, **bold**, or *italic* (including across newlines)
    INLINE_PATTERN = re.compile(
        r"(\*\*\*.+?\*\*\*|\*\*.+?\*\*|\*[^*\n]+?\*)",
        re.DOTALL,
    )

    def __init__(self, font_manager=None):
        self.font_manager = font_manager or FontManager()
        self.colors = {
            "text": "#202020",
            "heading": "#111111",
            "hr": "#999999",
        }

    # --------------------------------------------------
    # Block parsing (supports multi-line lists & ordered lists)
    # --------------------------------------------------
    def parse_blocks(self, markdown_text: str):
        blocks = []
        paragraph_lines = []
        list_items = []  # list of {"marker": str, "lines": list[str]}
        list_ordered = False

        def flush_paragraph():
            if paragraph_lines:
                blocks.append({"type": "paragraph", "text": "\n".join(paragraph_lines)})
                paragraph_lines.clear()

        def flush_list():
            if list_items:
                blocks.append(
                    {
                        "type": "list",
                        "ordered": list_ordered,
                        "items": [
                            {"marker": item["marker"], "text": "\n".join(item["lines"])}
                            for item in list_items
                        ],
                    }
                )
                list_items.clear()

        for raw_line in markdown_text.splitlines():
            stripped = raw_line.strip()

            if not stripped:
                flush_paragraph()
                flush_list()
                continue

            if self.HR_PATTERN.match(stripped):
                flush_paragraph()
                flush_list()
                blocks.append({"type": "hr"})
                continue

            heading_match = self.HEADING_PATTERN.match(stripped)
            if heading_match:
                flush_paragraph()
                flush_list()
                blocks.append(
                    {
                        "type": "heading",
                        "level": len(heading_match.group(1)),
                        "text": heading_match.group(2).strip(),
                    }
                )
                continue

            ul_match = self.UL_PATTERN.match(stripped)
            if ul_match:
                flush_paragraph()
                if list_items and list_ordered:
                    flush_list()
                list_ordered = False
                list_items.append({"marker": "•", "lines": [ul_match.group(1).strip()]})
                continue

            ol_match = self.OL_PATTERN.match(stripped)
            if ol_match:
                flush_paragraph()
                if list_items and not list_ordered:
                    flush_list()
                list_ordered = True
                list_items.append(
                    {
                        "marker": f"{ol_match.group(1)}.",
                        "lines": [ol_match.group(2).strip()],
                    }
                )
                continue

            # Indented continuation line inside an active list item
            if list_items and raw_line.startswith((" ", "\t")):
                list_items[-1]["lines"].append(stripped)
                continue

            flush_list()
            paragraph_lines.append(stripped)

        flush_paragraph()
        flush_list()
        return blocks

    # --------------------------------------------------
    # Inline parsing (bold, italic, bold_italic)
    # --------------------------------------------------
    def parse_inline(self, text: str) -> list[TextRun]:
        parts = self.INLINE_PATTERN.split(text)
        runs = []

        for part in parts:
            if not part:
                continue
            if part.startswith("***") and part.endswith("***") and len(part) > 6:
                runs.append(TextRun(part[3:-3], bold=True, italic=True))
            elif part.startswith("**") and part.endswith("**") and len(part) > 4:
                runs.append(TextRun(part[2:-2], bold=True, italic=False))
            elif part.startswith("*") and part.endswith("*") and len(part) > 2:
                runs.append(TextRun(part[1:-1], bold=False, italic=True))
            else:
                runs.append(TextRun(part, bold=False, italic=False))

        return runs or [TextRun(text)]

    # --------------------------------------------------
    # Core wrapping & baseline-aligned drawing
    # --------------------------------------------------
    def draw_wrapped_runs(
        self,
        draw,
        runs: list[TextRun],
        x: float,
        y: float,
        max_width: float,
        size: int,
        heading: bool = False,
        align: str = "left",
    ) -> float:
        line_height = max(1, int(size * 1.55))
        lines = []  # each line = list of [text, bold, italic]
        current_line = []
        current_width = 0.0

        def get_font(bold: bool, italic: bool):
            return self.font_manager.get_text_font(
                size, bold=(bold or heading), italic=italic
            )

        def measure(text: str, bold: bool, italic: bool) -> float:
            return draw.textlength(text, font=get_font(bold, italic))

        def append_token(line_list, token_text: str, bold: bool, italic: bool):
            if line_list and line_list[-1][1] == bold and line_list[-1][2] == italic:
                line_list[-1][0] += token_text
            else:
                line_list.append([token_text, bold, italic])

        for run in runs:
            bold = run.bold or heading
            italic = run.italic
            tokens = re.findall(r"\n|[^\S\n]+|\S+", run.text)

            for token in tokens:
                if not token:
                    continue

                if token == "\n":
                    lines.append(current_line)
                    current_line = []
                    current_width = 0.0
                    continue

                if not current_line and token.isspace():
                    continue

                if (
                    current_line
                    and current_line[-1][1] == bold
                    and current_line[-1][2] == italic
                ):
                    prev_text = current_line[-1][0]
                    added_width = measure(prev_text + token, bold, italic) - measure(
                        prev_text, bold, italic
                    )
                else:
                    added_width = measure(token, bold, italic)

                if not current_line or current_width + added_width <= max_width:
                    append_token(current_line, token, bold, italic)
                    current_width += added_width
                    continue

                lines.append(current_line)
                current_line = []
                current_width = 0.0

                if token.isspace():
                    continue

                token_width = measure(token, bold, italic)

                if token_width > max_width:
                    remaining = token
                    while remaining:
                        best = 1
                        for i in range(1, len(remaining) + 1):
                            if measure(remaining[:i], bold, italic) <= max_width:
                                best = i
                            else:
                                break

                        piece = remaining[:best]
                        append_token(current_line, piece, bold, italic)
                        current_width = measure(piece, bold, italic)
                        remaining = remaining[best:]

                        if remaining:
                            lines.append(current_line)
                            current_line = []
                            current_width = 0.0
                else:
                    append_token(current_line, token, bold, italic)
                    current_width = token_width

        if current_line:
            lines.append(current_line)

        color = self.colors["heading"] if heading else self.colors["text"]

        # Calculate a shared baseline so regular, bold, and italic align cleanly
        base_ascent, _ = get_font(heading, False).getmetrics()

        for line in lines:
            if line and line[-1][0].endswith(" "):
                line[-1][0] = line[-1][0].rstrip(" ")

            line_width = sum(measure(t, b, it) for t, b, it in line)

            if align == "center":
                curr_x = x + max(0, (max_width - line_width) / 2)
            else:
                curr_x = x

            for text, bold, italic in line:
                if not text:
                    continue
                font = get_font(bold, italic)
                ascent, _ = font.getmetrics()
                draw.text(
                    (curr_x, y + (base_ascent - ascent)),
                    text,
                    font=font,
                    fill=color,
                )
                curr_x += measure(text, bold, italic)

            y += line_height

        return y

    # --------------------------------------------------
    # Public render method
    # --------------------------------------------------
    def render(self, draw, md_text, start_x, start_y, max_width, base_size=20):
        y = start_y
        blocks = self.parse_blocks(md_text)

        for block in blocks:
            if block["type"] == "heading":
                level = block["level"]
                size = max(base_size, int(base_size * (1.85 - level * 0.13)))
                y = self.draw_wrapped_runs(
                    draw,
                    self.parse_inline(block["text"]),
                    start_x,
                    y,
                    max_width,
                    size,
                    heading=True,
                    align="center",
                )
                y += int(size * 0.7)

            elif block["type"] == "list":
                indent = int(base_size * 1.6)
                marker_font = self.font_manager.get_text_font(base_size, bold=True)

                for item in block["items"]:
                    draw.text(
                        (start_x + 4, y),
                        item["marker"],
                        font=marker_font,
                        fill=self.colors["text"],
                    )
                    y = self.draw_wrapped_runs(
                        draw,
                        self.parse_inline(item["text"]),
                        start_x + indent,
                        y,
                        max_width - indent,
                        base_size,
                    )
                    y += int(base_size * 0.25)

                y += int(base_size * 0.2)

            elif block["type"] == "hr":
                y += 10
                draw.line(
                    [(start_x, y), (start_x + max_width, y)],
                    fill=self.colors["hr"],
                    width=2,
                )
                y += 18

            else:  # paragraph
                y = self.draw_wrapped_runs(
                    draw,
                    self.parse_inline(block["text"]),
                    start_x,
                    y,
                    max_width,
                    base_size,
                )
                y += int(base_size * 0.45)

        return y
