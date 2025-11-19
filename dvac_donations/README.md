# DVAC Donations MCP Server

This MCP server is designed to extract donation data from PDF files using AI vision capabilities. It converts PDFs to images and uses the OpenRouter API with Google's Gemini model to extract structured donation information.

## Overview

The server provides two tools:
- `extract_and_parse_donations`: Processes PDF files and extracts key donation details including:
  - Donor name(s)
  - Address
  - Donation amount
  - Date
- `save_results_to_csv`: Saves the extracted donation data to a CSV file.

## Features

- Converts PDF files to optimized images for processing for `extract_and_parse_donations` tool.
- Uses Google's Gemini 2.5 Flash model via OpenRouter for accurate data extraction.
- Processes up to 5 files at a time using `extract_and_parse_donations` to avoid timeout issues.
- Handles post-processing of extracted data (e.g., ensuring addresses are single-line) directly within the server tools.
- Provides a dedicated `save_results_to_csv` tool for saving aggregated results to a CSV file.
- Includes detailed error handling and logging.

## Requirements

- Python 3.8+
- Poppler library for PDF processing
- OpenRouter API key
- Required Python packages (see `requirements.txt`)

## Installation

1.  **Create and activate a Python Virtual Environment** (recommended):
    ```bash
    python -m venv venv
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

2.  **Install the required Python packages** within the active virtual environment:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Poppler**:
    -   Download Poppler for Windows: https://github.com/oschwartz10612/poppler-windows/releases/
    -   Extract to a directory (e.g., `C:\poppler-25.11.0\`)
    -   Update the `POPPLER_PATH` variable in `dvac_donations_server.py` if your path is different.

4.  **Set up environment variables**:
    -   Copy `.env.template` to `.env` in the `dvac_donations/` directory.
    -   Add your OpenRouter API key to the newly created `.env` file.

## Usage

1. Start the server from within your activated virtual environment:
   ```bash
   python dvac_donations_server.py
   ```

2. Utilize the recommended prompt structure (found at the top of `dvac_donations_server.py`) with your AI coding assistant to process files and save results. The overall workflow involves:
   a.  Identifying a list of PDF file paths.
   b.  Calling the **`extract_and_parse_donations`** tool in batches (maximum 5 files per call) to process the PDFs.
   c.  Collecting and combining the results from all processed batches.
   d.  Calling the **`save_results_to_csv`** tool with the combined results and your desired output CSV file path.

   ```python
   # Example pseudo-code for LLM interaction:
   # 1. Get file paths (e.g., by listing files in a directory)
   # ALL_PDF_FILES = ["/path/to/doc1.pdf", "/path/to/doc2.pdf", ...]
   # combined_donation_data = []

   # 2. Process in batches
   # for i in range(0, len(ALL_PDF_FILES), 5):
   #     current_batch = ALL_PDF_FILES[i : i + 5]
   #     batch_results_json = use_mcp_tool(
   #         "dvac_donations",
   #         "extract_and_parse_donations",
   #         {"file_paths": current_batch, "max_pages": 1}
   #     )
   #     batch_results_list = json.loads(batch_results_json)
   #     combined_donation_data.extend(batch_results_list)

   # 3. Save combined results to CSV
   # save_status = use_mcp_tool(
   #     "dvac_donations",
   #     "save_results_to_csv",
   #     {"data": combined_donation_data, "output_file": "/path/to/your_output.csv"}
   # )
   # print(save_status)
   ```

## Important Notes

-   **No Helper Scripts:** All processing for extraction and CSV output must occur either within the `dvac_donations` MCP server's tools or directly via LLM calls. The creation or use of external helper scripts (Python, Bash, PowerShell, etc.) for this workflow is strictly prohibited.
-   **Batch Processing:** It is critical to process PDF files in batches of 5 or fewer when using the `extract_and_parse_donations` tool to adhere to MCP timeout limits.
-   **Image Optimization:** The server optimizes images (resizing, grayscale conversion, compression) generated from PDFs to reduce API payload size.
-   **Consistent Output:** The AI model is prompted to return extracted data in a specific, consistent JSON format.
-   **Address Formatting:** Address fields are automatically post-processed by the tools to ensure they are single-line strings before being saved to CSV.

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

To use this MCP server with Roo Code, add the following configuration to your MCP settings. Replace `PATH_TO_YOUR_dvac_donations` with the absolute path to your `dvac_donations` directory (e.g., `C:\MCP-Tools\dvac_donations`).

```json
{
  "mcpServers": {
    "dvac_donations": {
      "command": "PATH_TO_YOUR_dvac_donations/venv/Scripts/python",
      "args": ["PATH_TO_YOUR_dvac_donations/dvac_donations_server.py"],
      "env": {
        "OPENROUTER_API_KEY": "your_openrouter_api_key"
      }
    }
  }
}
```

### Cursor

To integrate with Cursor, add the following configuration to `~/.cursor/mcp.json` or `.cursor/mcp.json` in your project folder. Replace `PATH_TO_YOUR_dvac_donations` as described above.

```json
{
  "mcpServers": {
    "dvac_donations": {
      "command": "PATH_TO_YOUR_dvac_donations/venv/Scripts/python",
      "args": ["PATH_TO_YOUR_dvac_donations/dvac_donations_server.py"]
    }
  }
}
```

### Claude Code

For Claude Code, add the following configuration to your `CLAUDE.md` file or MCP configuration. Replace `PATH_TO_YOUR_dvac_donations` as described above.

```json
{
  "mcp": {
    "servers": {
      "dvac_donations": {
        "type": "stdio",
        "command": "PATH_TO_YOUR_dvac_donations/venv/Scripts/python",
        "args": ["PATH_TO_YOUR_dvac_donations/dvac_donations_server.py"]
      }
    }
  }
}
```

### General Integration Steps

1.  Ensure you have followed the **Installation** steps, including creating and activating the virtual environment, and setting up your environment variables (especially `OPENROUTER_API_KEY`).
2.  Add the appropriate configuration JSON, carefully replacing `PATH_TO_YOUR_dvac_donations` with the actual absolute path to your `dvac_donations` directory (e.g., `C:\MCP-Tools\dvac_donations`), to your AI coding assistant's MCP configuration file.
3.  Restart your AI coding assistant to load the new MCP server.
4.  The server will automatically start when needed by your assistant.
5.  Follow the **Usage** guidelines to employ the `extract_and_parse_donations` and `save_results_to_csv` tools with your coding assistant when working with donation PDFs.

Note: The exact configuration file location and format may vary depending on your AI coding assistant version. Refer to your assistant's documentation for specific MCP integration instructions.