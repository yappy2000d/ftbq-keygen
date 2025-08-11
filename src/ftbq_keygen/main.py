import argparse
import re
import uuid
import json
import logging
from dataclasses import dataclass
from typing import Callable, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

TITLE_CAPTURE_RE = re.compile(r'title:\s*"(.+?)"')
DESC_ARRAY_RE = re.compile(r'description:\s*\[(?:\s*)?(?:"[^"]*"(?:\s*)?)+\]')
QUOTED_STR_RE = re.compile(r'"(.+?)"')


@dataclass
class KeyGenerator:
    """Generates unique localization keys and accumulates them."""

    lang_dict: Dict[str, str]
    char_count: Dict[str, int]
    prefix: str = "ftbq_keygen"

    def __call__(self, text: str) -> str:
        key = f"{self.prefix}.{uuid.uuid5(uuid.NAMESPACE_DNS, text).hex}"
        self.lang_dict[key] = text
        self.char_count[key] = len(text)
        return "{" + key + "}"


def replace_title(ctx: str, gen: Callable[[str], str]) -> str:
    """replaces title content with a generated key."""

    def repl(m: re.Match) -> str:
        src = m.group(1)
        dst = gen(src)
        return f'title: "{dst}"'

    return TITLE_CAPTURE_RE.sub(repl, ctx)


def replace_description(ctx: str, gen: Callable[[str], str]) -> str:
    """replaces description content with generated keys."""

    def replace_array(m: re.Match) -> str:
        array_text = m.group(0)

        def replace_string(sm: re.Match) -> str:
            src = sm.group(1)
            return f'"{gen(src)}"'

        return QUOTED_STR_RE.sub(replace_string, array_text)

    return DESC_ARRAY_RE.sub(replace_array, ctx)


def process_file(file_path: Path) -> Tuple[Path, Dict[str, str], Dict[str, int]]:
    logger = logging.getLogger("ftbq_keygen")
    logger.info(file_path)

    lang_dict: Dict[str, str] = {}
    char_count: Dict[str, int] = {}
    gen = KeyGenerator(lang_dict, char_count)

    ctx = Path(file_path).read_text(encoding="utf-8")
    ctx = replace_title(ctx, gen)
    ctx = replace_description(ctx, gen)

    Path(file_path).write_text(ctx, encoding="utf-8")
    return file_path, lang_dict, char_count


def main():
    parser = argparse.ArgumentParser(
        description="Generate localization keys for FTB Quests."
    )
    parser.add_argument(
        "-f", "--folder", type=str, required=True, help="Path to the ftbquests folder."
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show detailed processing log."
    )
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format="%(message)s", level=log_level)
    logger = logging.getLogger("ftbq_keygen")

    folder = Path(args.folder)

    if not folder.is_dir():
        logger.error(f"Error: {folder} is not a valid directory.")
        return

    files = list(folder.glob("**/*.snbt"))
    logger.info(f"Found {len(files)} files to process.")

    all_lang: Dict[str, str] = {}
    all_char_count: Dict[str, int] = {}
    with ThreadPoolExecutor() as executor:
        results = executor.map(process_file, files)
        for result in results:
            file_path, lang_dict, char_count = result
            logger.debug(f"Processed: {file_path}")
            all_lang.update(lang_dict)
            all_char_count.update(char_count)

    with open("lang.json", "w", encoding="utf-8") as f:
        json.dump(all_lang, f, ensure_ascii=False, indent=4)

    logger.info("ALL Done!")
    logger.info(f"Processed {len(files)} files.")
    logger.info(f"Total unique keys: {len(all_lang)}")
    logger.info(f"Total character count: {sum(all_char_count.values())}")


if __name__ == "__main__":
    main()
