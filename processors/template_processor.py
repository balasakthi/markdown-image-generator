import logging

from pathlib import Path

from models.template_config import TemplateConfig


logger = logging.getLogger(__name__)


class TemplateProcessor:
    def __init__(self, markdown_provider, image_processor, output_folder: Path):

        self.markdown_provider = markdown_provider
        self.image_processor = image_processor
        self.output_folder = output_folder

    def process_template(self, template: TemplateConfig):

        logger.info("Starting template processing: %s", template.name)

        markdown_files = self.markdown_provider.get_matching_files(template.name)

        if not markdown_files:
            logger.warning("No Markdown files found for template: %s", template.name)

            return

        successful = 0
        failed = 0

        for markdown_path in markdown_files:
            try:
                self.image_processor.process(
                    template, markdown_path, self.output_folder
                )

                successful += 1

            except Exception:
                failed += 1

                logger.exception("Failed to process: %s", markdown_path.name)

        logger.info(
            "Template '%s' completed | Successful: %d | Failed: %d",
            template.name,
            successful,
            failed,
        )

    def process_all(self, templates):

        for template in templates:
            self.process_template(template)
