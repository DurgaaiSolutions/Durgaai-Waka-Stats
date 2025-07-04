from os.path import join, isfile
from pickle import load as load_pickle, dump as dump_pickle
from typing import Optional, Any


class FileManager:
    ASSETS_DIR = "assets"

    @staticmethod
    def write_file(name: str, content: str, append: bool = False, assets: bool = False):
        name = join(FileManager.ASSETS_DIR, name) if assets else name
        with open(name, "a" if append else "w", encoding="utf-8") as file:
            file.write(content)

    @staticmethod
    def cache_binary(name: str, content: Optional[Any] = None, assets: bool = False) -> Optional[Any]:
        name = join(FileManager.ASSETS_DIR, name) if assets else name
        if content is None and not isfile(name):
            return None

        with open(name, "rb" if content is None else "wb") as file:
            if content is None:
                try:
                    return load_pickle(file)
                except Exception:
                    return None
            else:
                dump_pickle(content, file)
                return None
