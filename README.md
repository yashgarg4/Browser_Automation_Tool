# Browser Automation Tool

A collection of Python scripts designed to scrape game information from popular web game portal like CrazyGames.com. The tool extracts details for top games within a specified genre and saves the data neatly into an Excel file.

## Features

- **Site Scraping**: Currently supports scraping from:
  - [CrazyGames.com](https://www.crazygames.com/)
- **Genre-Specific Search**: Fetches top games based on a user-provided genre.
- **Detailed Data Extraction**: Gathers key information for each game, including:
  - Game Name
  - Game URL
  - Developer
  - Rating and Vote Count
  - Platform (for CrazyGames)
- **Automated Excel Export**: Saves all the scraped data into a timestamped `.xlsx` file for easy analysis.

---

## Installation

Follow these steps to set up the project on your local machine.

### Prerequisites

- Python 3.8+
- Git

### 1. Clone the Repository

Open your terminal or command prompt and clone this repository.

```bash
git clone https://github.com/YOUR_USERNAME/game-scraper-suite.git
cd game-scraper-suite
```

_(Replace `YOUR_USERNAME` with your actual GitHub username)_

### 2. Create and Activate a Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create the virtual environment
python -m venv venv

# Activate it (on Windows)
.\venv\Scripts\activate

# Activate it (on macOS/Linux)
source venv/bin/activate
```

### 3. Install Dependencies

Install all the required Python packages from the `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Install Playwright Browsers

Playwright requires browser binaries to be installed. This command will download them.

```bash
playwright install
```

---

## Usage

You can run each scraper individually from your terminal. Make sure your virtual environment is activated.

### Scraping from CrazyGames.com

To run the CrazyGames scraper, execute the `app.py` script. You will be prompted to enter a game genre.

```bash
python app.py
```

After a script finishes, a new `.xlsx` file containing the scraped data will be saved in the project's root directory.
