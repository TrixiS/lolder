from pathlib import Path


def get_dir(path):
    """
    Функция возвращает директорию файла, если он является файлом, иначе
    возвращает объект Path из указанного пути
    """
    if not isinstance(path, Path):
        path = Path(path)

    return path.parent if path.is_file() else path
