# Disclaimer
For self-learning purposes only, not to be used for any commercial purposes.

# Technical Architecture

- Utilize Selenium and Chrome Driver for dynamic web scraping of government examination information for various provinces and cities from the target website.
- Process the scraped data and store it in a cloud database or Meilisearch search engine. Use Azure GPT to recognize and parse the deadline information in the announcements.
- Employ FastAPI to offer web services for user authentication and querying government examination information. This service is specifically designed for storage and querying using Meilisearch. If a database is used, the functionality will be handled by cloud functions from Unicloud.

