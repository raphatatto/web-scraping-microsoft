import time
import json
import logging
from playwright.sync_api import sync_playwright

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_job_details(page):
    job_details = {}
    try:
        title_element = page.query_selector('div.ms-DocumentCard h1')
        job_details['title'] = title_element.inner_text().strip() if title_element else 'No title found'

        location_element = page.query_selector('div.ms-Stack-inner p')
        job_details['location'] = location_element.inner_text().strip() if location_element else 'No location found'

        identifier_element = page.query_selector('div.IyCDaH20Khhx15uuQqgx div:has-text("Job number")')
        job_details['jobId'] = identifier_element.inner_text().strip() if identifier_element else 'No Identifier found'

        workarea_element = page.query_selector('div.IyCDaH20Khhx15uuQqgx div:has-text("Profession")')
        job_details['workArea'] = workarea_element.inner_text().strip() if workarea_element else 'No Area found'

        application_url_element = page.query_selector('button.ms-Button')
        job_details['applyURL'] = application_url_element.get_attribute('href') if application_url_element else 'No application URL found'

        description_element = page.query_selector('div.MKwm2_A5wy0mMoh9vTuX:has(h3:has-text("Overview")) ~ div')
        job_details['description'] = description_element.inner_text().strip() if description_element else 'No description found'


        minimum_qualifications_element = page.query_selector('div.section:has(h2:has-text("BASIC QUALIFICATIONS")) p')
        job_details['minimumQualifications'] = minimum_qualifications_element.inner_text().strip() if minimum_qualifications_element else 'No description found'
        
        preferred_qualifications_element = page.query_selector('div.section:has(h2:has-text("PREFERRED QUALIFICATIONS")) p')
        job_details['preferredQualifications'] = preferred_qualifications_element.inner_text().strip() if preferred_qualifications_element else 'No description found'

        job_details['company'] = 'Amazon'

        json_ld_element = page.query_selector('script[type="application/ld+json"]')
        if json_ld_element:
            json_data = json_ld_element.inner_text()
            try:
                schema_data = json.loads(json_data)
                job_details['jsonSchema'] = schema_data
            except json.JSONDecodeError:
                print("Error decoding JSON-LD schema")
        
        logging.debug("Extracted job details")
    except Exception as e:
        logging.error("Error extracting job details: %s", e)

    return job_details

def scrape_jobs(max_pages=1):
    job_listings = []
    page_counter = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://jobs.careers.microsoft.com/global/en/search?l=en_us&pg=1&pgSz=20&o=Relevance&flt=true&ref=cms')
        logging.info("Navigated to job listings page")

        while True:
            try:
                page.wait_for_selector('div.ms-List-cell')
                listing_elements = page.query_selector_all('div.ms-List-cell')
                logging.info(f"Found {len(listing_elements)} job listing elements on page {page_counter + 1}")

                for listing in listing_elements:
                    card_element = listing.query_selector('div.ms-DocumentCard')
                    if card_element and card_element.is_visible():
                        try:
                            card_element.click()
                            page.wait_for_selector('div.ms-DocumentCard h1', timeout=10000)

                            job_details = extract_job_details(page)
                            job_listings.append(job_details)

                            page.go_back()
                            page.wait_for_selector('div.ms-List-cell', timeout=10000)
                            time.sleep(1)
                        except Exception as e:
                            logging.error("Error processing listing: %s", e)
                            continue

                page_counter += 1
                if page_counter >= max_pages:
                    break

                next_button = page.query_selector('button[aria-label="Go to next page"]')
                if next_button and not next_button.is_disabled():
                    next_button.click()
                    page.wait_for_timeout(2000)
                else:
                    break

            except Exception as e:
                logging.error("Error during scraping: %s", e)
                break

        browser.close()

    with open('microsoft_job_listings.json', 'w', encoding='utf-8') as f:
        json.dump({'listings': job_listings}, f, indent=2, ensure_ascii=False)

    logging.info('Job listings have been scraped and saved to microsoft_job_listings.json')

scrape_jobs(max_pages=1)
