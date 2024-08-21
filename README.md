# Quality and Work Status Report

### **Project Objective**
The objective of this script is to perform web scraping of all job listings available on the Microsoft careers website, extract detailed information about each job, and save the collected data in a JSON file.

### **Overall Process Description**
The script utilizes the Playwright library to automate navigation on the Microsoft careers site. It extracts the following details for each job listing:

- **Job Title**
- **Location**
- **Job Identifier (Job ID) and Work Area**
- **Application URL**
- **Job Description**
- **Responsibilities**
- **Qualifications**
- **Benefits**
- **Company Name**
- **Embedded JSON Schema from the page**

The extracted data is then stored in a JSON file named `microsoft_job_listings.json`.

### **Data Quality**
- **Job Title**: Consistent extraction, correctly capturing job titles.
- **Location**: Mostly captured correctly. Some jobs may not have a specific location and are recorded as "No location found."
- **Identifier and Work Area**: Correctly captured in most cases. If the information is unavailable, the script returns "No Identifier found" or "No Area found."
- **Application URL**: The script captures the application URL in most cases. If the URL is not found, the script returns "No apply URL found."
- **Description, Responsibilities, and Qualifications**: These fields are correctly extracted, but formatting or the presence of line breaks may result in less readable data. The script attempts to mitigate this by removing explicit line breaks.
- **Benefits**: Successfully captured when available. Otherwise, "No benefits found" is returned.
- **Company Name**: Since the script is specific to the Microsoft site, the company name is fixed as "Microsoft."
- **JSON Schema**: The script attempts to capture the embedded JSON-LD from the page. In case of decoding failure, the error is logged, and the field may be omitted.

### **Work Status**
- **Completeness**: The script was executed until all available job listing pages were exhausted. No critical errors were encountered that would prevent the script's full execution.
- **Performance**: The script ran efficiently, but the total execution time may be long due to the high number of jobs (over 3300) and the need to navigate through multiple pages.
- **Resilience**: Error handling measures were implemented to capture exceptions and continue the scraping process, minimizing disruption in case of temporary failures.
- **Output**: The `microsoft_job_listings.json` file was successfully generated and contains all job listings collected during the process.

### **Recommendations**
- **Additional Validation**: A manual review of the collected data may be necessary to ensure total accuracy, especially for jobs with complex text formatting.
- **Future Optimizations**: To improve performance, consider using asynchronous scraping or parallelism, especially for large data volumes.
- **Continuity**: The script can be used on a recurring basis but should be updated if there are changes to the structure of the Microsoft page.

---

This report provides an overview of the status and quality of the work performed, and the generated JSON file is ready to be used or reviewed by other team members.
