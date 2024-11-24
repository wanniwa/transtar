from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ParatranzProgress:
    translate: float
    review: float
    check: float


@dataclass
class ParatranzFile:
    id: int
    name: str
    folder: str
    format: str
    total: int
    translated: int
    disputed: int
    checked: int
    reviewed: int
    words: int
    progress: ParatranzProgress

    @property
    def filename(self) -> str:
        return self.name.split('/')[-1]

    @property
    def folder_path(self) -> str:
        return '/'.join(self.name.split('/')[:-1])


@dataclass
class ParatranzFolder:
    name: str
    files: List[ParatranzFile]
    total_entries: int = 0
    total_words: int = 0

    def calculate_totals(self):
        self.total_entries = sum(f.total for f in self.files)
        self.total_words = sum(f.words for f in self.files)


class ParatranzFileManager:
    @staticmethod
    def organize_files(files: List[dict]) -> Dict[str, ParatranzFolder]:
        folders = {}

        for file_data in files:
            paratranz_file = ParatranzFile(
                id=file_data['id'],
                name=file_data['name'],
                folder=file_data['folder'],
                format=file_data['format'],
                total=file_data['total'],
                translated=file_data['translated'],
                disputed=file_data['disputed'],
                checked=file_data['checked'],
                reviewed=file_data['reviewed'],
                words=file_data['words'],
                progress=ParatranzProgress(**file_data['progress'])
            )

            folder_name = paratranz_file.folder_path
            if folder_name not in folders:
                folders[folder_name] = ParatranzFolder(folder_name, [])

            folders[folder_name].files.append(paratranz_file)

        # Calculate totals for each folder
        for folder in folders.values():
            folder.calculate_totals()

        return folders
