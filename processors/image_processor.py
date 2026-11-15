import logging

from pathlib import Path
from PIL import Image, ImageDraw

from models.template_config import TemplateConfig
from renderers.markdown_renderer import MarkdownRenderer

logger = logging.getLogger(__name__)


class ImageProcessor:
    def __init__(
        self,
        markdown_provider,
        markdown_renderer: MarkdownRenderer,
        min_font_size: int = 10,
    ):

        self.markdown_provider = markdown_provider
        self.markdown_renderer = markdown_renderer
        self.min_font_size = min_font_size

    def process(
        self, template: TemplateConfig, markdown_path: Path, output_folder: Path
    ):

        # 1. Read Markdown
        markdown_content = self.markdown_provider.read(markdown_path)

        # 2. Validate template
        if not template.template_path.is_file():
            raise FileNotFoundError(f"Template not found: {template.template_path}")

        # 3. Open template
        with Image.open(template.template_path) as image:
            img = image.convert("RGB")

            left, top, right, bottom = template.box_coords

            # Validate coordinates
            if not (0 <= left < right <= img.width and 0 <= top < bottom <= img.height):
                raise ValueError(
                    f"Invalid coordinates for {template.name}: {template.box_coords}"
                )

            box_width = right - left
            box_height = bottom - top

            margin = 20

            content_width = box_width - margin * 2
            content_height = box_height - margin * 2

            if content_width <= 0 or content_height <= 0:
                raise ValueError(f"Template box is too small: {template.name}")

            # 4. Clear original content area
            draw = ImageDraw.Draw(img)

            draw.rectangle(template.box_coords, fill="white")

            # 5. Render and automatically reduce font size
            selected_font_size = template.font_size
            rendered_overlay = Image.new("RGBA", (box_width, box_height), (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(rendered_overlay)

            self.markdown_renderer.render(
                draw=overlay_draw,
                md_text=markdown_content,
                start_x=margin,
                start_y=margin,
                max_width=content_width,
                base_size=selected_font_size,
            )

            # 6. Fail if content still doesn't fit
            if rendered_overlay is None:
                raise ValueError(
                    f"Markdown content cannot fit inside template "
                    f"'{template.name}' even at minimum font size "
                    f"{self.min_font_size}."
                )

            # 7. Paste rendered content onto template
            img.paste(rendered_overlay, (left, top), rendered_overlay)

            # 8. Save generated image
            output_folder.mkdir(parents=True, exist_ok=True)

            output_path = output_folder / f"{markdown_path.stem}.png"

            img.save(output_path)

            logger.info(
                "Generated %s successfully using font size %d",
                output_path.name,
                selected_font_size,
            )

            return output_path
