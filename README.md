# Amazon Review Scraper

## Usage
1. Install the Chrome Extension from `/src/Chrome Extension/`

2. `pip install -r requirements.txt`

3. To configure CSV file upload to your Google Drive place a config.json and client_secret.json in project root

   `config.json:`
     ```
        {
        "DRIVE_ACCESS":
            {
                "FOLDER_ID":"<Your-Google-Drive-Folder-ID>"
            }
        }
    ```
4. Finally `python run.py`
5. From Chrome extension click on "Send URL"

#### NOTE: This repository is only for educational purposes.