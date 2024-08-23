import time
import json
import logging
from urllib.parse import quote
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
        if 'jobId' in job_details and 'title' in job_details:
            encoded_title = quote(job_details['title'])
            job_url = f'https://jobs.careers.microsoft.com/global/en/job/{job_details["jobId"]}/{encoded_title}'
            job_details['url'] = job_url
        else:
            job_details['url'] = 'No URL constructed'

        # Capture Job Description without explicit line breaks
        description_elements = page.query_selector_all('div.MKwm2_A5wy0mMoh9vTuX div.ms-Stack:has(h3:has-text("Overview")) p')
        description = " ".join([element.inner_text().strip().replace('\n', ' ') for element in description_elements])
        job_details['description'] = description if description else 'No description found'

        # Capture Responsibilities without explicit line breaks
        responsibilities_elements = page.query_selector_all('div.MKwm2_A5wy0mMoh9vTuX div.ms-Stack:has(h3:has-text("Responsibilities")) div')
        responsibilities = " ".join([element.inner_text().strip().replace('\n', ' ') for element in responsibilities_elements])
        job_details['responsibilities'] = responsibilities if responsibilities else 'No responsibilities found'

        # Capture Minimum Qualifications (adjusted as per the specific requirement)
        qualification_section = page.query_selector('div.WzU5fAyjS4KUVs1QJGcQ')

        if qualification_section:
            # Capturar a primeira lista de qualificações (primeiro <ul> diretamente após a <p> ou <strong>)
            first_list = qualification_section.query_selector('ul:first-of-type')

            if first_list:
                # Extrair os itens dentro dessa lista
                qualification_items = first_list.query_selector_all('li > span')
                
                qualifications = []
                
                # Adicionar o conteúdo de cada item de lista capturado
                for item in qualification_items:
                    text_content = item.inner_text().strip()
                    if text_content:
                        qualifications.append(text_content)
                        
                job_details['minimumQualifications'] = " ".join(qualifications) if qualifications else 'No qualifications found'
            else:
                job_details['minimumQualifications'] = 'No qualifications found'
        else:
            job_details['minimumQualifications'] = 'No qualifications found'

        #Extract other requirements
        other_requirements_section = qualification_section.query_selector('ul:nth-of-type(2)')  # Assuming it is the second list in the same section
        if other_requirements_section:
            other_requirements_items = other_requirements_section.query_selector_all('li > span')
            other_requirements = [item.inner_text().strip() for item in other_requirements_items if item.inner_text().strip()]
            job_details['otherRequirements'] = " ".join(other_requirements) if other_requirements else ''
        else:
            job_details['otherRequirements'] = ''
        
        preferred_qualifications_section = qualification_section.query_selector('ul:nth-of-type(3)')  # Assuming it is the third list in the same section
        if preferred_qualifications_section:
            preferred_qualifications_items = preferred_qualifications_section.query_selector_all('li > span')
            preferred_qualifications = [item.inner_text().strip() for item in preferred_qualifications_items if item.inner_text().strip()]
            job_details['preferredQualifications'] = " ".join(preferred_qualifications) if preferred_qualifications else ''
        else:
            job_details['preferredQualifications'] = ''
        

        salary_section = page.query_selector('div.ms-Stack ul p')
        if salary_section:
            salary_text = salary_section.inner_text().strip()
            salary_links = salary_section.query_selector_all('a')
            links = [f"{link.inner_text().strip()}: {link.get_attribute('href')}" for link in salary_links]
            job_details['salary'] = f"{salary_text} {' '.join(links)}" if links else salary_text
        else:
            job_details['salary'] = ''
            
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
