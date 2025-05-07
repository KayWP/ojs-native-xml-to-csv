# OJS Native XML 3.3 to Intermediary CSV Exporter

This script parses OJS 3.3 (Open Journal Systems) XML export files and generates an intermediary `.csv` file that consolidates article metadata, author information, and embedded files into a structured format suitable for further processing or import, specifically with KNAW-HUC's [ojs-tools](https://github.com/knaw-huc/ojs-tools), to convert it from Native XML 3.3 to Native XML 3.4. This can assist in moving journals from a 3.3 installation to a 3.4 installation.

## Features

- Parses OJS 3.3 Native XML files.
- Extracts metadata for articles, issues, sections, and authors.
- Supports embedded base64-encoded files (e.g., manuscripts).
- Outputs a semicolon-separated CSV file (`output.csv`).
- Handles missing values gracefully with sensible defaults.
- Designed for automation and batch processing.

## Output Format

The script produces a `output.csv` file with columns for:

- Article metadata (`title`, `abstract`, `publication date`, `volume`, `issue`, `doi`, etc.)
- Author data (dynamically added columns for multiple authors)
- Base64 file content (embedded in the `file` column)
- Section titles and policies
- Keywords (semicolon-separated with `[;sep;]` marker)


## Requirements
- Pandas

## Usage

```bash
python Converter.py <xml_file>
```


