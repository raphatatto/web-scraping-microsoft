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
        detail_elements = page.query_selector_all('div.IyCDaH20Khhx15uuQqgx > div.ms-Stack')
        for element in detail_elements:
            # The second child contains the value in bold
            value_element = element.query_selector('div:nth-child(2)')
            value = value_element.inner_text().strip() if value_element else 'No value found'
            
            # Determine which title it is by its sibling
            title_element = element.query_selector('div:nth-child(1)')
            title = title_element.inner_text().strip() if title_element else 'No title found'
            
            if title == "Date posted":
                job_details['datePosted'] = value
            elif title == "Job number":
                job_details['jobId'] = value
            elif title == "Work site":
                job_details['workSite'] = value
            elif title == "Role type":
                job_details['roleType'] = value
            elif title == "Profession":
                job_details['profession'] = value
            elif title == "Employment type":
                job_details['employmentType'] = value
            elif title == "Travel":
                job_details['travel'] = value
            elif title == "Discipline":
                job_details['discipline'] = value

        

        # button for Application
        apply_button = page.query_selector('a[data-test-id="applyButton"]') 
        job_details['applyURL'] = apply_button.get_attribute('href') if apply_button else 'No apply URL found'

        # Capture Job Description without explicit line breaks
        description_elements = page.query_selector_all('div.MKwm2_A5wy0mMoh9vTuX div.ms-Stack:has(h3:has-text("Overview")) p')
        description = " ".join([element.inner_text().strip().replace('\n', ' ') for element in description_elements])
        job_details['description'] = description if description else 'No description found'

        # Capture Responsibilities without explicit line breaks
        responsibilities_elements = page.query_selector_all('div.MKwm2_A5wy0mMoh9vTuX div.ms-Stack ul')
        responsibilities = " ".join([element.inner_text().strip().replace('\n', ' ') for element in responsibilities_elements])
        job_details['responsibilities'] = responsibilities if responsibilities else 'No responsibilities found'

        # Capture Qualifications without explicit line breaks
        minimum_qualifications_elements = page.query_selector_all('div.WzU5fAyjS4KUVs1QJGcQ div.ms-Stack ul:nth-child(1)')
        qualifications = " ".join([element.inner_text().strip().replace('\n', ' ') for element in minimum_qualifications_elements])
        job_details['minimumQualifications'] = qualifications if qualifications else 'No qualifications found'

        other_requirements_elements = page.query_selector_all('div.WzU5fAyjS4KUVs1QJGcQ:has(p:has-text("Other Requirements"))ul')
        other_requirements = [loc.inner_text().strip() for loc in other_requirements_elements]
        job_details['otherRequirements'] = ', '.join(other_requirements)
        
        preferred_qualification_elements = page.query_selector_all('div.WzU5fAyjS4KUVs1QJGcQ:has(h3:has-text("Responsibilities"))div')
        preferred_qualification = [loc.inner_text().strip() for loc in preferred_qualification_elements]
        job_details['preferredRequirements'] = ', '.join(preferred_qualification)
        

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

        except Exception as e:
            logging.error("Error during scraping: %s", e)

        browser.close()

    with open('microsoft_job_listings.json', 'w', encoding='utf-8') as f:
        json.dump({'listings': job_listings}, f, indent=2, ensure_ascii=False)

    logging.info('Job listings have been scraped and saved to microsoft_job_listings.json')

scrape_jobs()
