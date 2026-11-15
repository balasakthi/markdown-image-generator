import json
import os

from pathlib import Path
from dotenv import load_dotenv
from models.template_config import TemplateConfig


class Settings:
    def __init__(self):
        load_dotenv()
        self.template_folder = Path(os.getenv("TEMPLATE_FOLDER", "templates"))
        self.markdown_folder = Path(os.getenv("MARKDOWN_FOLDER", "markdown"))
        self.output_folder = Path(os.getenv("OUTPUT_FOLDER", "output"))
        self.config_file = Path(os.getenv("CONFIG_FILE", "config/templates.json"))

    def validate(self):

        if not self.template_folder.is_dir():
            raise FileNotFoundError(
                f"Template folder not found: {self.template_folder}"
            )

        if not self.markdown_folder.is_dir():
            raise FileNotFoundError(
                f"Markdown folder not found: {self.markdown_folder}"
            )

        if not self.config_file.is_file():
            raise FileNotFoundError(f"Configuration file not found: {self.config_file}")

        self.output_folder.mkdir(parents=True, exist_ok=True)


class TemplateConfigLoader:
    def __init__(self, config_file, template_folder):
        self.config_file = config_file
        self.template_folder = template_folder

    def load(self):

        with self.config_file.open("r", encoding="utf-8") as file:
            configurations = json.load(file)

        templates = []

        for name, config in configurations.items():
            coordinates = config["box_coords"]

            if (
                not isinstance(coordinates, list)
                or len(coordinates) != 4
                or any(type(value) is not int for value in coordinates)
            ):
                raise ValueError(f"Invalid box coordinates for template: {name}")

            template = TemplateConfig(
                name=name,
                template_path=(self.template_folder / config["template"]),
                box_coords=tuple(coordinates),
                font_size=config.get("font_size", 20),
            )

            templates.append(template)

        return templates
