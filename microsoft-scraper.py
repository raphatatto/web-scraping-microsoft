import time
import json
import logging
from playwright.sync_api import sync_playwright

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_job_details(page):
    job_details = {}
    try:
        # Capture Job Title
        title_element = page.query_selector('div.ms-DocumentCard h1')
        job_details['title'] = title_element.inner_text().strip() if title_element else 'No title found'

        # Capture Location
        location_element = page.query_selector('div.ms-Stack-inner p')
        job_details['location'] = location_element.inner_text().strip() if location_element else 'No location found'

        # Capture Identifier and Work Area
        identifier_element = page.query_selector('div.IyCDaH20Khhx15uuQqgx div:has-text("Job number")')
        job_details['jobId'] = identifier_element.inner_text().strip().replace('\n', ' ') if identifier_element else 'No Identifier found'

        workarea_element = page.query_selector('div.IyCDaH20Khhx15uuQqgx div:has-text("Profession")')
        job_details['workArea'] = workarea_element.inner_text().strip().replace('\n', ' ') if workarea_element else 'No Area found'

        # Capture APPLY URL
        apply_button = page.query_selector('button[aria-label="Apply"]')
        job_details['applyURL'] = apply_button.get_attribute('href') if apply_button else 'No apply URL found'

        # Capture other details as before...

        logging.debug("Extracted job details")
    except Exception as e:
        logging.error("Error extracting job details: %s", e)

    return job_details

def scrape_jobs():
    job_listings = []
    page_counter = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        while True:
            try:
                page_counter += 1
                url = f'https://jobs.careers.microsoft.com/global/en/search?l=en_us&pg={page_counter}&pgSz=20&o=Relevance&flt=true&ref=cms'
                page.goto(url)
                logging.info(f"Navigated to job listings page {page_counter}")

                page.wait_for_selector('div.ms-List-cell')
                listing_elements = page.query_selector_all('div.ms-List-cell')
                logging.info(f"Found {len(listing_elements)} job listing elements on page {page_counter}")

                for listing in listing_elements:
                    card_element = listing.query_selector('div.ms-DocumentCard')
                    if card_element and card_element.is_visible():
                        try:
                            card_element.click()
                            page.wait_for_selector('div.ms-DocumentCard h1', timeout=60000)

                            job_details = extract_job_details(page)
                            job_listings.append(job_details)

                            page.go_back()
                            page.wait_for_selector('div.ms-List-cell', timeout=60000)
                            time.sleep(1)
                        except Exception as e:
                            logging.error("Error processing listing: %s", e)
                            continue

                # Check if there is a "Next Page" button available
                next_button = page.query_selector('button[aria-label="Go to next page"]')
                if not next_button or next_button.is_disabled():
                    logging.info(f"No more pages to process. Stopping at page {page_counter}.")
                    break

                logging.info(f"Completed page {page_counter}")

            except Exception as e:
                logging.error(f"Error during scraping on page {page_counter}: %s", e)
                break

        browser.close()

    # Save all job listings to a JSON file
    with open('all_job_listings.json', 'w', encoding='utf-8') as f:
        json.dump({'listings': job_listings}, f, indent=2, ensure_ascii=False)

    logging.info('All job listings have been scraped and saved to all_job_listings.json')

scrape_jobs()
