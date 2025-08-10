import argparse
import re
import uuid
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


def process_file(file_path):
    logger = logging.getLogger("ftbq_keygen")
    logger.info(file_path)

    lang_dict = {}
    char_count = {}

    def gen_uuid(text: str):
        key = f"ftbq_keygen.{uuid.uuid5(uuid.NAMESPACE_DNS, text).hex}"
        lang_dict[key] = text
        char_count[key] = len(text)
        return "{" + key + "}"

    def replace_title(ctx: str):
        titleRegex = r'title: ".*"'
        titleRegexStr = r'title: "(.+)"'
        titles = re.findall(titleRegex, ctx)
        for i in titles:
            src = re.match(titleRegexStr, i).group(1)  # pyright: ignore[reportOptionalMemberAccess]
            dst = gen_uuid(src)
            ctx = ctx.replace(i, i.replace(src, dst))
        return ctx

    def replace_desc(ctx: str):
        descRegex = r'description: \[(?:\s*)?(?:".*"(?:\s*)?)+\]'
        targets = re.findall(descRegex, ctx)
        for desc in targets:
            desc_old = desc
            srcs = re.findall('"(.+)"', desc)
            for src in srcs:
                dst = gen_uuid(src)
                desc = desc.replace(src, dst)
            ctx = ctx.replace(desc_old, desc)
        return ctx

    ctx = open(file_path, "r", encoding="utf-8").read()
    ctx = replace_title(ctx)
    ctx = replace_desc(ctx)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(ctx)
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

    all_lang = {}
    all_char_count = {}
    with ThreadPoolExecutor() as executor:
        results = executor.map(process_file, files)
        for result in results:
            file_path, lang_dict, char_count = result
            logger.debug(f"Processed: {file_path}")
            all_lang.update(lang_dict)
            all_char_count.update(char_count)

    json.dump(
        all_lang, open("lang.json", "w", encoding="utf-8"), ensure_ascii=False, indent=4
    )

    logger.info("ALL Done!")
    logger.info(f"Processed {len(files)} files.")
    logger.info(f"Total unique keys: {len(all_lang)}")
    logger.info(f"Total character count: {sum(all_char_count.values())}")


if __name__ == "__main__":
    main()
