import re
import zipfile
import shutil
from pathlib import Path

DIR = Path("/home/stos/Projekt_Inzynierski-2025/test_files/")
FILE = DIR / "sources-1347.zip"
DST = DIR / "submissions"


def lowercase_includes(root_dir: Path):
    """Zamienia wszystkie linie #include na lowercase w plikach źródłowych."""
    for file_path in root_dir.rglob("*"):
        if file_path.is_file() and file_path.suffix in {".c", ".h", ".cpp", ".hpp"}:
            with file_path.open("r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            new_lines = [
                line.lower() if line.lstrip().startswith("#include") else line
                for line in lines
            ]
            with file_path.open("w", encoding="utf-8") as f:
                f.writelines(new_lines)


def unzip_file(zip_path: Path, extract_to: Path):
    """Rozpakowuje plik ZIP do podanego folderu."""
    if extract_to.exists():
        shutil.rmtree(extract_to)
    extract_to.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)


def sanitize_filenames(root_dir: Path):
    """Zamienia nawiasy w nazwach plików i folderów na '_'."""
    for path in root_dir.rglob("*"):
        new_name = re.sub(r"[()]", "_", path.name)
        if new_name != path.name:
            new_path = path.with_name(new_name)
            path.rename(new_path)


def zip_subfolders(root_dir: Path):
    """Zipuje wszystkie podfoldery w root_dir i usuwa oryginalne foldery."""
    for folder in root_dir.iterdir():
        if folder.is_dir():
            zip_path = root_dir / f"{folder.name}.zip"
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for file_path in folder.rglob("*"):
                    arcname = file_path.relative_to(folder)
                    zf.write(file_path, arcname)
            shutil.rmtree(folder)


if __name__ == "__main__":
    unzip_file(FILE, DST)
    sanitize_filenames(DST)
    lowercase_includes(DST)
    zip_subfolders(DST)
