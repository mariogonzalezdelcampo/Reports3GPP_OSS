# 3GPP Report Generator

A Python application to automatically generate reports for 3GPP SA5 Charging subgroup follow-up meetings.

## Overview

This application automates the process of downloading, extracting, and processing 3GPP meeting documents. It specifically targets the SA5 Charging subgroup meetings and generates structured reports from the meeting documentation.

## Features

- Automatically downloads meeting documents from the 3GPP website
- Extracts and processes Excel files to filter relevant items
- Downloads and extracts TDoc documents referenced in the meeting agenda
- Generates structured summary reports in Markdown format
- Robust error handling and input validation
- Configurable meeting numbers and output directories

## Requirements

- Python 3.7+
- Required packages (see `requirements.txt`)

## Installation

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The application can be configured through:
1. A `config.toml` file in the project root
2. Environment variables
3. Command-line arguments

### Configuration Options

**config.toml**:
```toml
# Meeting number to process (e.g., 165)
meeting_number = 165

# Directory where documents will be downloaded and processed
documents_dir = "./documents"

# Temporary directory for downloads
temp_dir = "./temp"
```

**Environment Variables**:
- `MEETING_NUMBER`: Override meeting number
- `DOCS_DIR`: Override documents directory
- `CONFIG_PATH`: Override config file path

## Usage

### Command Line

```bash
# Run with default configuration
python src/main.py

# Run with specific meeting number
python src/main.py 165

# Run with environment variable override
MEETING_NUMBER=166 python src/main.py
```

### Programmatic Usage

```python
from src.main import main

# Run with default configuration
main()

# Run with specific meeting number
main(meeting_number=165)
```

## Output Structure

The application creates the following directory structure:
```
documents/
└── 3GPP_meeting_docs_165/
    ├── TDoc_List_Meeting165.zip
    ├── Meeting165.xlsx
    ├── Meeting165.csv
    ├── FS_6G_CH/
    │   ├── Summary.md
    │   └── [TDoc files]
    └── [other WIs directories]
```

## Error Handling

The application includes comprehensive error handling:
- Network connectivity issues
- File I/O errors
- Invalid configuration values
- Missing or corrupted files
- HTML parsing failures

## Security Considerations

- All network requests include timeouts
- File paths are validated to prevent path traversal
- Input validation prevents malformed data
- Temporary files are cleaned up automatically

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- 3GPP for providing the meeting documentation
- Python community for excellent libraries