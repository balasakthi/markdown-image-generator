import re

from pathlib import Path


class MarkdownFileProvider:
    def __init__(self, markdown_folder: Path):
        self.markdown_folder = markdown_folder

    def get_matching_files(self, template_name: str):

        pattern = re.compile(rf"^{re.escape(template_name)}-(\d+)\.md$", re.IGNORECASE)

        matching_files = []

        for filepath in self.markdown_folder.iterdir():
            if not filepath.is_file():
                continue

            match = pattern.match(filepath.name)

            if match:
                matching_files.append((int(match.group(1)), filepath))

        # Numeric sorting: 1, 2, 3, 10
        matching_files.sort(key=lambda item: item[0])

        return [filepath for _, filepath in matching_files]

    def read(self, filepath: Path):

        if not filepath.is_file():
            raise FileNotFoundError(f"Markdown file not found: {filepath}")

        return filepath.read_text(encoding="utf-8")
