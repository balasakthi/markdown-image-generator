from functools import lru_cache
from pathlib import Path

from PIL import ImageFont


class FontManager:
    FONT_DIRECTORY = Path(__file__).resolve().parents[1] / "assets" / "fonts"

    FONT_FILES = {
        "regular": "NotoSans-Regular.ttf",
        "bold": "NotoSans-Bold.ttf",
        "italic": "NotoSans-Italic.ttf",
        "bold_italic": "NotoSans-BoldItalic.ttf",
    }

    def __init__(self, font_directory=None):

        self.font_directory = (
            Path(font_directory).resolve() if font_directory else self.FONT_DIRECTORY
        )

        self.validate_fonts()

    # --------------------------------------------------
    # GET FONT PATH
    # --------------------------------------------------
    def get_font_path(self, style: str) -> Path:

        if style not in self.FONT_FILES:
            raise ValueError(f"Unsupported font style: {style}")

        font_path = self.font_directory / self.FONT_FILES[style]

        if not font_path.is_file():
            raise FileNotFoundError(f"Required font not found: {font_path}")

        return font_path

    # --------------------------------------------------
    # LOAD FONT
    # --------------------------------------------------
    @lru_cache(maxsize=256)
    def get_font(self, size: int, style: str = "regular") -> ImageFont.FreeTypeFont:

        if size <= 0:
            raise ValueError("Font size must be greater than zero.")

        font_path = self.get_font_path(style)
        font = ImageFont.truetype(
            str(font_path),
            size=size,
            layout_engine=ImageFont.Layout.BASIC,
        )

        print(f"STYLE: {style:<12} FONT: {font.getname()} PATH: {font_path.name}")

        return font

    # --------------------------------------------------
    # TEXT FONTS
    # --------------------------------------------------
    def get_text_font(self, size: int, bold: bool = False, italic: bool = False):

        if bold and italic:
            style = "bold_italic"

        elif bold:
            style = "bold"

        elif italic:
            style = "italic"

        else:
            style = "regular"

        return self.get_font(size, style)

    # --------------------------------------------------
    # VALIDATE ALL FONTS
    # --------------------------------------------------
    def validate_fonts(self):

        print("\n========== FONT VALIDATION ==========")

        for style in self.FONT_FILES:
            font_path = self.get_font_path(style)

            # Verify that Pillow can actually load the font
            ImageFont.truetype(str(font_path), size=20)

            print(f"[OK] {style:<12} -> {font_path.name}")

        print("All custom fonts loaded successfully.")
        print("=====================================\n")
