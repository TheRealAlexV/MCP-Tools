# DVAC Donations MCP Server

This MCP server is designed to extract donation data from PDF files using AI vision capabilities. It converts PDFs to images and uses the OpenRouter API with Google's Gemini model to extract structured donation information.

## Overview

The server provides a tool called `extract_and_parse_donations` that processes PDF files and extracts key donation details including:
- Donor name(s)
- Address
- Donation amount
- Date

## Features

- Converts PDF files to optimized images for processing
- Uses Google's Gemini 2.5 Flash model via OpenRouter for accurate data extraction
- Processes up to 5 files at a time to avoid timeout issues
- Handles post-processing of extracted data (e.g., ensuring addresses are single-line)
- Provides detailed error handling and logging

## Requirements

- Python 3.8+
- Poppler library for PDF processing
- OpenRouter API key
- Required Python packages (see `requirements.txt`)

## Installation

1. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. Install Poppler:
   - Download Poppler for Windows: https://github.com/oschwartz10612/poppler-windows/releases/
   - Extract to a directory (e.g., `C:\poppler-25.11.0\`)
   - Update the `POPPLER_PATH` in `dvac_donations_server.py` if needed

3. Set up environment variables:
   - Copy `.env.template` to `.env`
   - Add your OpenRouter API key to the `.env` file

## Usage

1. Start the server:
   ```bash
   python dvac_donations_server.py
   ```

2. Use the `extract_and_parse_donations` tool with a list of PDF file paths:
   ```python
   # Example usage
   file_paths = [
       "/path/to/donation1.pdf",
       "/path/to/donation2.pdf"
   ]
   result = extract_and_parse_donations(file_paths, max_pages=1)
   ```

## Important Notes

- Process files in batches of 5 or fewer to avoid MCP timeout limits
- The server optimizes images (resizing, grayscale conversion, compression) to reduce API payload size
- The AI model is prompted to return data in a specific JSON format for consistency
- Address fields are post-processed to ensure they are single-line strings

## Customization

You can modify the following aspects of the server:
- Prompt instructions in the `extract_and_parse_donations` function for different extraction requirements
- Image optimization parameters (DPI, quality, resize dimensions)
- Output format by modifying the JSON structure in the prompt

## Error Handling

The server includes comprehensive error handling:
- PDF conversion errors
- API call failures
- JSON parsing issues
- File access problems

Errors are returned in the response JSON for easy debugging.

## Integration with AI Coding Assistants

### Roo Code

To use this MCP server with Roo Code, add the following configuration to your MCP settings:

```json
{
  "mcpServers": {
    "dvac_donations": {
      "command": "python",
      "args": ["PATH_TO_YOUR_dvac_donations/dvac_donations_server.py"],
      "env": {
        "OPENROUTER_API_KEY": "your_openrouter_api_key"
      }
    }
  }
}
```

### Cursor

To integrate with Cursor, add the following configuration to `~/.cursor/mcp.json` or `.cursor/mcp.json` in your project folder:

```json
{
  "mcpServers": {
    "dvac_donations": {
      "command": "python",
      "args": ["PATH_TO_YOUR_dvac_donations/dvac_donations_server.py"]
    }
  }
}
```

### Claude Code

For Claude Code, add the following configuration to your `CLAUDE.md` file or MCP configuration:

```json
{
  "mcp": {
    "servers": {
      "dvac_donations": {
        "type": "stdio",
        "command": "python",
        "args": ["PATH_TO_YOUR_dvac_donations/dvac_donations_server.py"]
      }
    }
  }
}
```

### General Integration Steps

1. Ensure you have set up your environment variables (especially `OPENROUTER_API_KEY`) as described in the Installation section
2. Add the appropriate configuration JSON to your AI coding assistant's MCP configuration file
3. Restart your AI coding assistant to load the new MCP server
4. The server will automatically start when needed by your assistant
5. Use the `extract_and_parse_donations` tool directly from your coding assistant when working with donation PDFs

Note: The exact configuration file location and format may vary depending on your AI coding assistant version. Refer to your assistant's documentation for specific MCP integration instructions.