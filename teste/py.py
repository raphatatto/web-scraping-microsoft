import time
import json
import re
import logging
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

# Initialize logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_text(text):
    # Remove tags HTML
    text = re.sub(r'<[^>]+>', text)
    # Remove quebras de linha e espaços extras
    text = re.sub(r'\s+', text).strip()
    return text

# Function to extract job details from the job detail page
def extract_job_details(page):
    job_details = {}

    try:
        # Extract Title
        title_element = page.query_selector('h1.app-title')
        job_details['jobtitle'] = title_element.inner_text().strip() if title_element else 'No title found'

        # Extract Location
        location_element = page.query_selector('div.location')
        job_details['joblocation'] = location_element.inner_text().strip() if location_element else 'No location found'

        # Locate the #content element
        content_element = page.query_selector('#content')

        # Check for the 'p-rich_text_section' class inside the #content element
        rich_text_section = content_element.query_selector('.p-rich_text_section')

        # Use the rich_text_section if it exists; otherwise, use the content element itself
        target_element = rich_text_section if rich_text_section else content_element

        # Extract Description (all <p> elements before the first <ul>)
        description_elements = []
        
        
        # Iterate over all child elements in #content
        for element in target_element.query_selector_all('*'):
            tag_name = element.evaluate('(el) => el.tagName', element).lower()
            if tag_name == 'ul':
                break
            if tag_name == 'p':
                description_elements.append(element.inner_text().strip())
            if tag_name == 'div':
                description_elements.append(element.inner_text().strip())

        job_details['briefJobDescription'] = description_elements if description_elements else 'No description found'


        # Extract Responsibilities (only the first <ul> within #content)
        responsibilities_ul = page.query_selector('#content ul:first-of-type')
        if responsibilities_ul:
            responsibilities_elements = responsibilities_ul.query_selector_all('li')
            job_details['responsibilities'] = [el.inner_text().strip() for el in responsibilities_elements]
        else:
            job_details['responsibilities'] = 'No responsibilities found'

        # Extract Qualifications (only the second <ul> within #content)
        qualifications_ul = page.query_selector('#content ul:nth-of-type(2)')
        if qualifications_ul:
            qualifications_elements = qualifications_ul.query_selector_all('li')
            job_details['qualifications'] = [el.inner_text().strip() for el in qualifications_elements]
        else:
            job_details['qualifications'] = 'No qualifications found'

        # Select all <ul> elements within the #content element
        ul_elements = page.query_selector_all('#content ul')

        # Get the last <ul> element
        if ul_elements:
            last_ul = ul_elements[-1]
            
            # Find all <p> elements after the last <ul> element
            salary_paragraphs = last_ul.query_selector_all('~ p')
            
            # Filter out any paragraphs that contain only non-breaking spaces or are empty
            filtered_paragraphs = [
                el.inner_text().strip() 
                for el in salary_paragraphs 
                if el.inner_text().strip() and "&nbsp;" not in el.inner_text()
            ]
            
            # Check the number of filtered <p> elements after the last <ul>
            if len(filtered_paragraphs) >= 2:
                # If there are at least two <p> elements, get the last two
                job_details['salaryRange'] = " ".join(filtered_paragraphs[-2:])
            elif len(filtered_paragraphs) == 1:
                # If there's only one relevant <p> element, get that one
                job_details['salaryRange'] = filtered_paragraphs[-1]
            else:
                # If no relevant paragraphs are found, return a default message
                job_details['salaryRange'] = 'No salary found'
        else:
            # If no <ul> elements found, look for the last <p> elements directly
            salary_elements = page.query_selector_all('#content p')
            
            filtered_paragraphs = [
                el.inner_text().strip() 
                for el in salary_elements 
                if el.inner_text().strip() and "&nbsp;" not in el.inner_text()
            ]
            
            # Handle based on the number of filtered <p> elements found
            if len(filtered_paragraphs) >= 2:
                job_details['salaryRange'] = " ".join(filtered_paragraphs[-2:])
            elif len(filtered_paragraphs) == 1:
                job_details['salaryRange'] = filtered_paragraphs[-1]
            else:
                job_details['salaryRange'] = 'No salary found'

        # Extract "About Grafana Labs"
        job_details['about'] = 'There are more than 20M users of Grafana, the open source visualization tool, around the globe, monitoring everything from beehives to climate change in the Alps. The instantly recognizable dashboards have been spotted everywhere from a NASA launch and Minecraft HQ to Wimbledon and the Tour de France. Grafana Labs also helps more than 3,000 companies -- including Bloomberg, JPMorgan Chase, and eBay -- manage their observability strategies with the Grafana LGTM Stack, which can be run fully managed with Grafana Cloud or self-managed with the Grafana Enterprise Stack, both featuring scalable metrics (Grafana Mimir), logs (Grafana Loki), and traces (Grafana Tempo).'

        # Extract Benefits
        job_details['benefits'] = 'For more information about the perks and benefits of working at Grafana, please check out our careers page.'

        # Extract "Equal Opportunity Employer"
        job_details['opportunity'] = ' At Grafana Labs we’re building a company where a diverse mix of talented people want to come, stay, and do their best work. We know that our company runs on the hard work and the dedication of our passionate and creative employees. If you’re excited about this role but your experience doesn’t align perfectly with every qualification in the job description, we encourage you to apply anyways. We will recruit, train, compensate and promote regardless of race, religion, color, national origin, gender, disability, age, veteran status, and all the other fascinating characteristics that make us different and unique. We believe that equality and diversity builds a strong organization and we’re working hard to make sure that’s the foundation of our organization as we grow.'

        # Extract Application URL
        application_url_element = page.query_selector('#apply_button')
        apply_url = application_url_element.get_attribute('href') if application_url_element else 'No application URL found'
        job_details['applyURL'] = urljoin(page.url, apply_url) if application_url_element else 'No application URL found'

        job_details['company'] = 'Grafana'

        # Extract JSON-LD Schema
        json_ld_element = page.query_selector('script[type="application/ld+json"]')
        if json_ld_element:
            json_data = json_ld_element.inner_text()
            try:
                schema_data = json.loads(json_data)
                job_details['jsonSchema'] = schema_data  # Append the entire JSON-LD as a nested dictionary
            except json.JSONDecodeError:
                logging.error("Error decoding JSON-LD schema")
        
        logging.debug("Extracted job details")

        # Print job details as a JSON object to the console
        print(json.dumps(job_details, indent=4))

    except Exception as e:
        logging.error("Error extracting job details: %s", e)

    return job_details

def scrape_jobs(max_pages=1):
    job_listings = []
    page_counter = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto('https://grafana.com/about/careers/open-positions/')
        logging.info("Navigated to job listings page")

        while True:
            try:
                # Wait for the job listings to load
                page.wait_for_selector('div.col')

                # Find all job listing elements
                listing_elements = page.query_selector_all('div.col')
                logging.info(f"Found {len(listing_elements)} job listing elements on page {page_counter + 1}")

                # Extract details for each job listing
                for listing in listing_elements:
                    href = listing.query_selector('a.card-resource').get_attribute('href')
                    if href:
                        try:
                            job_url = href
                            new_page = browser.new_page()
                            new_page.goto(job_url)
                            new_page.wait_for_selector('h1.app-title', timeout=10000)
                            job_details = extract_job_details(new_page)
                            job_listings.append(job_details)
                            new_page.close()
                            time.sleep(1)
                        except Exception as e:
                            logging.error("Error processing listing: %s", e)
                            continue

                # Increment page counter
                page_counter += 1
                if page_counter >= max_pages:
                    break

                # Check for the next page button and navigate
                next_button = page.query_selector('button[aria-label="Next page"]')
                if next_button and not next_button.is_disabled():
                    next_button.click()
                    page.wait_for_timeout(2000)  # Adjust this as necessary for the page to load
                else:
                    break

            except Exception as e:
                logging.error("Error during scraping: %s", e)
                break

        browser.close()

    # Save the job listings to a JSON file
    with open('grafana_job_listings.json', 'w', encoding='utf-8') as f:
        json.dump({'listings': job_listings}, f, indent=2, ensure_ascii=False)

    logging.info('Job listings have been scraped and saved to grafana_job_listings.json')

# Execute the scraping function with a limit of 2 pages for testing
scrape_jobs(max_pages=1)