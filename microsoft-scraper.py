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

        # URL for Application
        apply_button = page.query_selector('a[data-test-id="applyButton"]') 
        job_details['applyURL'] = apply_button.get_attribute('href') if apply_button else 'No apply URL found'


        # Capture Job Description without explicit line breaks
        description_elements = page.query_selector_all('div.MKwm2_A5wy0mMoh9vTuX div.ms-Stack p')
        description = " ".join([element.inner_text().strip().replace('\n', ' ') for element in description_elements])
        job_details['description'] = description if description else 'No description found'

        # Capture Responsibilities without explicit line breaks
        responsibilities_elements = page.query_selector_all('div.MKwm2_A5wy0mMoh9vTuX div.ms-Stack ul')
        responsibilities = " ".join([element.inner_text().strip().replace('\n', ' ') for element in responsibilities_elements])
        job_details['responsibilities'] = responsibilities if responsibilities else 'No responsibilities found'

        # Capture Qualifications without explicit line breaks
        qualifications_elements = page.query_selector_all('div.WzU5fAyjS4KUVs1QJGcQ')
        qualifications = " ".join([element.inner_text().strip().replace('\n', ' ') for element in qualifications_elements])
        job_details['Qualifications'] = qualifications if qualifications else 'No qualifications found'
        
        # Capture all Benefits
        benefits_elements = page.query_selector_all('div.KDE7kZPL_kjXdvl00Oro > span')
        benefits = [element.inner_text().strip().replace('\n', ' ') for element in benefits_elements]
        job_details['benefits'] = benefits if benefits else ['No benefits found']

        # Capture Company Name
        job_details['company'] = 'Microsoft'

        # Capture JSON Schema
        json_ld_element = page.query_selector('script[type="application/ld+json"]')
        if json_ld_element:
            json_data = json_ld_element.inner_text()
            try:
                schema_data = json.loads(json_data)
                job_details['jsonSchema'] = schema_data
            except json.JSONDecodeError:
                logging.error("Error decoding JSON-LD schema")
        
        logging.debug("Extracted job details")
    except Exception as e:
        logging.error("Error extracting job details: %s", e)

    return job_details

def scrape_jobs():
    job_listings = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://jobs.careers.microsoft.com/global/en/search?l=en_us&pg=1&pgSz=20&o=Relevance&flt=true&ref=cms')
        logging.info("Navigated to job listings page")

        while True:
            try:
                page.wait_for_selector('div.ms-List-cell')
                listing_elements = page.query_selector_all('div.ms-List-cell')
                logging.info(f"Found {len(listing_elements)} job listing elements on current page")

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

                # Try to move to the next page
                next_button = page.query_selector('button[aria-label="Go to next page"]')
                if next_button and not next_button.is_disabled():
                    next_button.click()
                    page.wait_for_timeout(2000)
                else:
                    logging.info("No more pages to process. Stopping.")
                    break

            except Exception as e:
                logging.error("Error during scraping: %s", e)
                break

        browser.close()

    with open('microsoft_job_listings.json', 'w', encoding='utf-8') as f:
        json.dump({'listings': job_listings}, f, indent=2, ensure_ascii=False)

    logging.info('Job listings have been scraped and saved to microsoft_job_listings.json')

scrape_jobs()
