# FTB Quest - Localization Keys Generator

A tool to generate localization keys for FTB Quests.

## Features

- Extracts text from FTB Quest files
- Generates unique localization keys
- Supports multiple languages

## Usage

> [!WARNING]
> program will overwrite the original files with the updated content. You may want to create a backup copy of your files before running the tool.

```bash
ftbq-keygen -f /path/to/ftbquests
```

you should see a `lang.json` file generated in the current directory, containing all the localization keys generated from the program. You can then use this file to manage translations for your mod.

