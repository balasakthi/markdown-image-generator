import logging
import sys

from config.settings import Settings, TemplateConfigLoader
from providers.markdown_provider import MarkdownFileProvider
from renderers.font_manager import FontManager
from renderers.markdown_renderer import MarkdownRenderer
from processors.image_processor import ImageProcessor
from processors.template_processor import TemplateProcessor


# Logging configuration
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class Application:
    def run(self):

        # 1. Load settings
        settings = Settings()

        settings.validate()

        # 2. Load template configurations
        config_loader = TemplateConfigLoader(
            settings.config_file, settings.template_folder
        )

        templates = config_loader.load()

        # 3. Initialize providers
        markdown_provider = MarkdownFileProvider(settings.markdown_folder)

        # 4. Initialize font manager
        font_manager = FontManager()

        font_manager.validate_fonts()

        # 5. Initialize Markdown renderer
        markdown_renderer = MarkdownRenderer(font_manager=font_manager)

        # 6. Initialize image processor
        image_processor = ImageProcessor(
            markdown_provider, markdown_renderer, min_font_size=10
        )

        # 7. Initialize template processor
        template_processor = TemplateProcessor(
            markdown_provider, image_processor, settings.output_folder
        )

        # 8. Process all templates
        template_processor.process_all(templates)


if __name__ == "__main__":
    try:
        Application().run()

        logger.info("All image processing tasks completed.")

    except Exception:
        logger.exception("Application execution failed.")
        sys.exit(1)
