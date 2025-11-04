This tool is a rough-and-ready text aligner for translators.

To use this tool, you need to put it in a folder together with two parallel texts (one is the translation of the other) in .txt format.

This easiest way to run this script is to use [uv](https://docs.astral.sh/uv/) in a terminal: `uv run txt_tmx_aligner.py`

You will be prompted to:
1. Specify your source and target language codes (e.g. 'en' and 'fr');
2. Specify your file names (e.g. source-en.txt and target-fr.txt);
3. Give the translation memory a name or just press Enter to use the default.

You should obtain a valid TMX file, that you can import in favourite your CAT tool.
