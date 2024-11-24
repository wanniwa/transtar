from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime


@dataclass
class Progress:
    translate: float
    review: float
    check: float


@dataclass
class File:
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
    progress: Progress
    created_at: datetime
    updated_at: datetime
    modified_at: datetime
    hash: str

    @property
    def filename(self) -> str:
        return self.name.split('/')[-1]

    @property
    def folder_path(self) -> str:
        return '/'.join(self.name.split('/')[:-1])


@dataclass
class Folder:
    name: str
    files: List[File]
    total_entries: int = 0
    total_words: int = 0

    def calculate_totals(self):
        self.total_entries = sum(f.total for f in self.files)
        self.total_words = sum(f.words for f in self.files)


class FileManager:
    @staticmethod
    def organize_files(files: List[dict]) -> Dict[str, Folder]:
        folders = {}

        for file_data in files:
            progress = Progress(**file_data['progress'])
            file = File(
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
                progress=progress,
                created_at=datetime.fromisoformat(file_data['createdAt'].replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(file_data['updatedAt'].replace('Z', '+00:00')),
                modified_at=datetime.fromisoformat(file_data['modifiedAt'].replace('Z', '+00:00')),
                hash=file_data['hash']
            )

            folder_name = file.folder_path
            if folder_name not in folders:
                folders[folder_name] = Folder(folder_name, [])

            folders[folder_name].files.append(file)

        # Calculate totals for each folder
        for folder in folders.values():
            folder.calculate_totals()

        return folders
