from dotenv import load_dotenv
from crawler import scrape_website

if __name__ == "__main__":
    load_dotenv()
    scrape_website()