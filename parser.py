import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor
import re
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import logging
from urllib.parse import urljoin, quote
import json


# Set up logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InternationalJobParser:
    # Class for parsing jobs from different websites
    
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0',
        ]
    
    @staticmethod
    def clean_text(text):
        if not text:
            return ''
        text = ' '.join(text.split())
        return text.strip()
        
    def get_session(self):
        session = requests.Session()
        
        retry = Retry(
            total=3, 
            backoff_factor=1.5, 
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry)
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        session.headers.update({
            'User-Agent': random.choice(self.user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9,de;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Charset': 'utf-8',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        return session

    def parse_indeed(self, query, location, start_page=0, max_pages=1):
        jobs = []
        logger.info(f"Searching Indeed: '{query}' in '{location}'")

        try:
            session = self.get_session()
            # Set cookie to avoid blocking
            session.cookies.set('CTK', 'test_cookie_value')

            # Loop through pages
            for page in range(start_page, start_page + max_pages):
                try:
                    # Indeed uses start parameter for pagination
                    start = page * 10
                    url = f"https://de.indeed.com/jobs?q={quote(query)}&l={quote(location)}&start={start}"
                    logger.info(f"📡 Indeed page {page + 1}")
                    
                    # Get the page
                    response = session.get(url, timeout=20)
                    response.encoding = 'utf-8'
                    
                    # Check status
                    if response.status_code != 200:
                        logger.warning(f"❌ Status {response.status_code}")
                        time.sleep(random.uniform(10, 15))
                        continue

                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find job containers (multiple selectors for reliability)
                    job_containers = soup.find_all('div', class_='job_seen_beacon')
                    
                    if not job_containers:
                        job_containers = soup.find_all('div', {'data-jk': True})
                    
                    if not job_containers:
                        job_containers = soup.find_all('td', class_='resultContent')
                    
                    if not job_containers:
                        job_containers = soup.find_all('div', {'class': lambda x: x and 'cardOutline' in str(x)})
                    
                    logger.info(f"📦 Found {len(job_containers)} jobs")

                    # Process each job
                    for idx, container in enumerate(job_containers[:15]):
                        try:
                            # Extract job title
                            title = None
                            title_elem = container.find('h2', class_='jobTitle')
                            if title_elem:
                                title_link = title_elem.find(['a', 'span'])
                                title = self.clean_text(title_link.get_text(strip=True)) if title_link else self.clean_text(title_elem.get_text(strip=True))
                            
                            # Try another way if not found
                            if not title:
                                title_elem = container.find('a', {'id': lambda x: x and x.startswith('job_')})
                                if title_elem:
                                    title = self.clean_text(title_elem.get_text(strip=True))
                            
                            # Skip if no title
                            if not title or len(title) < 3:
                                continue

                            # Extract company
                            company = 'Not specified'
                            company_elem = container.find('span', {'data-testid': 'company-name'})
                            if not company_elem:
                                company_elem = container.find('span', class_='companyName')
                            if company_elem:
                                company = self.clean_text(company_elem.get_text(strip=True))

                            # Extract location
                            job_location = location
                            location_elem = container.find('div', {'data-testid': 'text-location'})
                            if not location_elem:
                                location_elem = container.find('div', class_='companyLocation')
                            if location_elem:
                                job_location = self.clean_text(location_elem.get_text(strip=True))

                            # Extract salary
                            salary = 'Not specified'
                            salary_elem = container.find('div', {'class': lambda x: x and 'salary' in str(x).lower()})
                            if not salary_elem:
                                salary_elem = container.find('span', {'data-testid': 'attribute_snippet_testid'})
                            if salary_elem:
                                salary = self.clean_text(salary_elem.get_text(strip=True))

                            # Extract job link
                            link = 'https://de.indeed.com'
                            link_elem = container.find('a', {'data-jk': True})
                            if not link_elem:
                                link_elem = container.find('a', {'id': lambda x: x and x.startswith('job_')})
                            
                            if link_elem:
                                job_id = link_elem.get('data-jk') or link_elem.get('id', '').replace('job_', '')
                                if job_id:
                                    link = f"https://de.indeed.com/viewjob?jk={job_id}"

                            # Extract description
                            desc_elem = container.find('div', class_='slider_container')
                            if not desc_elem:
                                desc_elem = container.find('div', {'class': lambda x: x and 'snippet' in str(x).lower()})
                            summary = self.clean_text(desc_elem.get_text(strip=True, separator=' '))[:400] if desc_elem else f'{title} at {company}'

                            # Add job to list
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': job_location,
                                'salary': salary,
                                'summary': summary,
                                'link': link,
                                'source': 'Indeed',
                                'posted_date': 'recent',
                                'is_recent': True,
                                'parsed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                            logger.info(f"✅ {title[:50]} @ {company}")

                        except Exception as e:
                            logger.debug(f"⚠️ Error with job {idx}: {e}")
                            continue

                    # Pause to not overload server
                    time.sleep(random.uniform(10, 15))

                except Exception as e:
                    logger.error(f"❌ Error on page {page}: {e}")
                    time.sleep(random.uniform(8, 12))
                    continue

        except Exception as e:
            logger.error(f"❌ Indeed error: {e}")

        logger.info(f"🎯 Indeed: {len(jobs)} jobs")
    
    def parse_linkedin(self, query, location, start_page=0, max_pages=1):
        jobs = []
        logger.info(f"Searching LinkedIn: '{query}' in '{location}'")

        try:
            session = self.get_session()
            # Set English language for LinkedIn
            session.headers['Accept-Language'] = 'en-US,en;q=0.9'

            # Loop through pages
            for page in range(start_page, start_page + max_pages):
                try:
                    start = page * 25
                    url = f"https://www.linkedin.com/jobs/search/?keywords={quote(query)}&location={quote(location)}&start={start}"
                    logger.info(f"📡 LinkedIn page {page + 1}")
                    
                    # Get the page
                    response = session.get(url, timeout=20)
                    response.encoding = 'utf-8'

                    # Check status
                    if response.status_code != 200:
                        logger.warning(f"❌ Status {response.status_code}")
                        time.sleep(random.uniform(10, 15))
                        continue

                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find job cards (multiple selectors for reliability)
                    job_cards = []
                    job_cards = soup.find_all('div', {'class': lambda x: x and 'base-card' in str(x)})
                    
                    if not job_cards:
                        job_cards = soup.find_all('div', {'class': lambda x: x and 'job-search-card' in str(x)})
                    
                    if not job_cards:
                        job_cards = soup.find_all('li', {'class': lambda x: x and 'result-card' in str(x)})
                    
                    logger.info(f"📦 Found {len(job_cards)} jobs")

                    # Process each card
                    for idx, card in enumerate(job_cards[:15]):
                        try:
                            # Extract title
                            title = None
                            title_elem = card.find('h3', {'class': lambda x: x and 'base-search-card__title' in str(x)})
                            if not title_elem:
                                title_elem = card.find('h3')
                            if not title_elem:
                                title_elem = card.find('a', {'class': lambda x: x and 'title' in str(x).lower()})
                            
                            if title_elem:
                                title = self.clean_text(title_elem.get_text(strip=True))
                            
                            if not title or len(title) < 3:
                                continue

                            # Extract company
                            company = 'Not specified'
                            company_elem = card.find('h4', {'class': lambda x: x and 'base-search-card__subtitle' in str(x)})
                            if not company_elem:
                                company_elem = card.find('a', {'class': lambda x: x and 'company' in str(x).lower()})
                            if company_elem:
                                company = self.clean_text(company_elem.get_text(strip=True))

                            # Extract location
                            job_location = location
                            location_elem = card.find('span', {'class': lambda x: x and 'job-search-card__location' in str(x)})
                            if location_elem:
                                job_location = self.clean_text(location_elem.get_text(strip=True))

                            # Extract salary
                            salary = 'Not specified'
                            salary_elem = card.find(string=re.compile(r'[\$€£]\s*\d'))
                            if salary_elem:
                                salary = self.clean_text(salary_elem.strip())

                            # Extract link
                            link = 'https://linkedin.com'
                            link_elem = card.find('a', {'class': lambda x: x and 'base-card__full-link' in str(x)})
                            if not link_elem:
                                link_elem = card.find('a', href=True)
                            
                            if link_elem and link_elem.get('href'):
                                href = link_elem['href']
                                if '?' in href:
                                    href = href.split('?')[0]
                                link = href

                            # Extract description
                            summary = self.clean_text(card.get_text(strip=True, separator=' '))[:400]

                            # Add job to list
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': job_location,
                                'salary': salary,
                                'summary': summary or f'{title} at {company}',
                                'link': link,
                                'source': 'LinkedIn',
                                'posted_date': 'recent',
                                'is_recent': True,
                                'parsed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                            logger.info(f"✅ {title[:50]} @ {company}")

                        except Exception as e:
                            logger.debug(f"⚠️ Error with card {idx}: {e}")
                            continue

                    # Pause
                    time.sleep(random.uniform(10, 15))

                except Exception as e:
                    logger.error(f"❌ Error on page {page}: {e}")
                    time.sleep(random.uniform(8, 12))
                    continue

        except Exception as e:
            logger.error(f"❌ LinkedIn error: {e}")

        logger.info(f"🎯 LinkedIn: {len(jobs)} jobs")
        return jobs

    def parse_stepstone(self, query, location, start_page=0, max_pages=1):
        jobs = []
        logger.info(f"Searching StepStone: '{query}' in '{location}'")

        try:
            session = self.get_session()
            # StepStone is in German - set language
            session.headers['Accept-Language'] = 'de-DE,de;q=0.9,en;q=0.8'

            for page in range(start_page, start_page + max_pages):
                try:
                    # Build URL for StepStone
                    url = f"https://www.stepstone.de/jobs/{quote(query)}/in-{quote(location)}?page={page + 1}"
                    logger.info(f"📡 StepStone page {page + 1}")
                    
                    # Get the page
                    response = session.get(url, timeout=20)
                    response.encoding = 'utf-8'

                    # Check status
                    if response.status_code != 200:
                        logger.warning(f"❌ Status {response.status_code}")
                        time.sleep(random.uniform(10, 15))
                        continue

                    # Parse HTML
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find job items (multiple selectors for reliability)
                    job_items = []
                    job_items = soup.find_all('article', {'data-at': 'job-item'})
                    
                    if not job_items:
                        job_items = soup.find_all('article', {'class': lambda x: x and 'listing-item' in str(x)})
                    
                    if not job_items:
                        job_items = soup.find_all('article', {'data-id': True})
                    
                    logger.info(f"📦 Found {len(job_items)} jobs")

                    # Process each job
                    for idx, item in enumerate(job_items[:15]):
                        try:
                            # Extract title
                            title = None
                            title_elem = item.find('a', {'data-at': 'job-item-title'})
                            if not title_elem:
                                title_elem = item.find(['h2', 'h3'])
                            if not title_elem:
                                title_elem = item.find('a', href=re.compile(r'/jobs/'))
                            
                            if title_elem:
                                title = self.clean_text(title_elem.get_text(strip=True))
                            
                            # Skip if no title
                            if not title or len(title) < 3:
                                continue

                            # Extract company
                            company = 'Not specified'
                            company_elem = item.find('a', {'data-at': 'job-item-company-name'})
                            if not company_elem:
                                company_elem = item.find('span', {'class': lambda x: x and 'company' in str(x).lower()})
                            if company_elem:
                                company = self.clean_text(company_elem.get_text(strip=True))

                            # Extract location
                            job_location = location
                            location_elem = item.find('span', {'data-at': 'job-item-location'})
                            if not location_elem:
                                location_elem = item.find('li', {'class': lambda x: x and 'location' in str(x).lower()})
                            if location_elem:
                                job_location = self.clean_text(location_elem.get_text(strip=True))

                            # Extract salary
                            salary = 'Not specified'
                            salary_elem = item.find(string=re.compile(r'€\s*\d|EUR'))
                            if salary_elem:
                                salary = self.clean_text(salary_elem.strip())

                            # Extract link
                            link = 'https://www.stepstone.de'
                            link_elem = item.find('a', {'data-at': 'job-item-title'})
                            if not link_elem:
                                link_elem = item.find('a', href=re.compile(r'/jobs/'))
                            
                            if link_elem and link_elem.get('href'):
                                href = link_elem['href']
                                if href.startswith('/'):
                                    link = f"https://www.stepstone.de{href}"
                                else:
                                    link = href

                            # Extract description
                            summary = self.clean_text(item.get_text(strip=True, separator=' '))[:400]

                            # Add job to list
                            jobs.append({
                                'title': title,
                                'company': company,
                                'location': job_location,
                                'salary': salary,
                                'summary': summary or f'{title} at {company}',
                                'link': link,
                                'source': 'StepStone',
                                'posted_date': 'recent',
                                'is_recent': True,
                                'parsed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            })
                            
                            logger.info(f"✅ {title[:50]} @ {company}")

                        except Exception as e:
                            logger.debug(f"⚠️ Error with job {idx}: {e}")
                            continue

                    # Pause
                    time.sleep(random.uniform(10, 15))

                except Exception as e:
                    logger.error(f"❌ Error on page {page}: {e}")
                    time.sleep(random.uniform(8, 12))
                    continue

        except Exception as e:
            logger.error(f"❌ StepStone error: {e}")

        logger.info(f"🎯 StepStone: {len(jobs)} jobs")
        return jobs

    def parse_eurojobs(self, query, location, start_page=0, max_pages=1):
        jobs = []
        logger.info(f"Searching EURES: '{query}' in '{location}'")

        try:
            session = self.get_session()
            url = f"https://eures.europa.eu/search-for-a-job?query={quote(query)}&location={quote(location)}"
            logger.info(f"📡 EURES")
            
            response = session.get(url, timeout=30)
            response.encoding = 'utf-8'

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                job_items = soup.find_all(['article', 'div'], {'class': lambda x: x and 'job' in str(x).lower()})
                
                logger.info(f"📦 Found {len(job_items)} potential jobs")
                
                for idx, item in enumerate(job_items[:10]):
                    try:
                        title_elem = item.find(['h2', 'h3', 'h4', 'a'])
                        if not title_elem:
                            continue
                        
                        title = self.clean_text(title_elem.get_text(strip=True))
                        if len(title) < 5:
                            continue

                        jobs.append({
                            'title': title,
                            'company': 'Various European Employers',
                            'location': location,
                            'salary': 'Not specified',
                            'summary': self.clean_text(item.get_text(strip=True, separator=' '))[:300],
                            'link': 'https://eures.europa.eu',
                            'source': 'EURES',
                            'posted_date': 'recent',
                            'is_recent': True,
                            'parsed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        })
                        
                        logger.info(f"✅ {title[:50]}")
                    except Exception as e:
                        logger.debug(f"⚠️ EURES card {idx} error: {e}")
                        continue

        except Exception as e:
            logger.error(f"❌ EURES error: {e}")

        logger.info(f"🎯 EURES: {len(jobs)} jobs")
        return jobs

    def parse_all_sites(self, query, location, sources, 
                       page=0, max_pages=1):
        all_jobs = []
        
        parser_map = {
            'indeed': self.parse_indeed,
            'linkedin': self.parse_linkedin,
            'stepstone': self.parse_stepstone,
            'eures': self.parse_eurojobs,
        }
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = {}
            
            for source in sources:
                if source in parser_map:
                    future = executor.submit(parser_map[source], query, location, page, max_pages)
                    futures[future] = source
            
            for future in futures:
                try:
                    jobs = future.result(timeout=180)
                    source_name = futures[future]
                    logger.info(f"✅ {source_name}: {len(jobs)} jobs")
                    all_jobs.extend(jobs)
                except Exception as e:
                    logger.error(f"❌ {futures[future]} error: {e}")

        logger.info(f"🎯 TOTAL: {len(all_jobs)} jobs from all sources")
        return all_jobs

    @staticmethod
    def filter_jobs(jobs, min_salary=None, 
                   experience_level=None, only_recent=True):
        filtered = []
        
        for job in jobs:
            if only_recent and not job.get('is_recent', False):
                continue
                
            if experience_level and experience_level != 'all':
                title_lower = job['title'].lower()
                if experience_level == 'junior':
                    if any(x in title_lower for x in ['senior', 'lead', 'principal', 'staff']):
                        continue
                elif experience_level == 'senior':
                    if any(x in title_lower for x in ['junior', 'trainee', 'intern', 'entry']):
                        continue
            
            if min_salary:
                try:
                    salary_text = job['salary'].lower()
                    numbers = re.findall(r'\d+', salary_text.replace(',', '').replace('.', ''))
                    if numbers:
                        job_salary = int(numbers[0])
                        if job_salary < min_salary:
                            continue
                except:
                    pass
            
            filtered.append(job)
        
        return filtered