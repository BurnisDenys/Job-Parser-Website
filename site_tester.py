import requests
import time
from typing import Dict, List, Tuple
from urllib.parse import urlparse
import random

class SiteTester:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        self.test_sites = {
            'indeed': 'https://de.indeed.com',
            'stepstone': 'https://www.stepstone.de', 
            'xing': 'https://www.xing.com/jobs'
        }

    def test_site_availability(self, site_name: str) -> Dict:
        """Тестує доступність сайту"""
        if site_name not in self.test_sites:
            return {'available': False, 'error': 'Unknown site'}
            
        url = self.test_sites[site_name]
        
        try:
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            
            return {
                'site': site_name,
                'url': url,
                'available': response.status_code == 200,
                'status_code': response.status_code,
                'response_time': response.elapsed.total_seconds(),
                'blocked': response.status_code == 403,
                'error': None if response.status_code == 200 else f'HTTP {response.status_code}'
            }
            
        except requests.exceptions.Timeout:
            return {
                'site': site_name,
                'url': url,
                'available': False,
                'status_code': None,
                'response_time': None,
                'blocked': False,
                'error': 'Timeout'
            }
        except Exception as e:
            return {
                'site': site_name,
                'url': url,
                'available': False,
                'status_code': None,
                'response_time': None,
                'blocked': False,
                'error': str(e)
            }

    def test_all_sites(self) -> Dict:
        """Тестує всі сайти"""
        results = {}
        
        for site_name in self.test_sites.keys():
            print(f"Testing {site_name}...")
            results[site_name] = self.test_site_availability(site_name)
            time.sleep(1)  # Пауза між запитами
            
        return results

    def validate_job_link(self, url: str) -> Dict:
        """Валідує посилання на вакансію"""
        try:
            parsed = urlparse(url)
            
            # Перевіряємо чи це валідний URL
            if not parsed.scheme or not parsed.netloc:
                return {
                    'valid': False,
                    'accessible': False,
                    'error': 'Invalid URL format'
                }
            
            # Тестуємо доступність
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
            }
            
            response = requests.head(url, headers=headers, timeout=5, allow_redirects=True)
            
            return {
                'valid': True,
                'accessible': response.status_code == 200,
                'status_code': response.status_code,
                'final_url': response.url,
                'redirected': response.url != url,
                'error': None if response.status_code == 200 else f'HTTP {response.status_code}'
            }
            
        except Exception as e:
            return {
                'valid': True,  # URL може бути валідним, але недоступним
                'accessible': False,
                'error': str(e)
            }

    def test_search_functionality(self, site_name: str, query: str, location: str) -> Dict:
        """Тестує функціональність пошуку на сайті"""
        if site_name not in self.test_sites:
            return {'success': False, 'error': 'Unknown site'}
            
        try:
            base_url = self.test_sites[site_name]
            
            # Формуємо URL пошуку для кожного сайту
            if site_name == 'indeed':
                search_url = f"{base_url}/jobs?q={query}&l={location}"
            elif site_name == 'stepstone':
                search_url = f"{base_url}/work/{query.replace(' ', '-')}-jobs-in-{location.lower()}"
            elif site_name == 'xing':
                search_url = f"{base_url}/search?keywords={query}&location={location}"
            else:
                return {'success': False, 'error': 'Unsupported site'}
            
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8'
            }
            
            response = requests.get(search_url, headers=headers, timeout=15)
            
            # Перевіряємо чи сторінка містить результати пошуку
            content = response.text.lower()
            has_jobs = any(keyword in content for keyword in ['job', 'stelle', 'position', 'karriere'])
            
            return {
                'site': site_name,
                'search_url': search_url,
                'success': response.status_code == 200,
                'status_code': response.status_code,
                'has_job_content': has_jobs,
                'blocked': response.status_code == 403,
                'response_size': len(response.content),
                'error': None if response.status_code == 200 else f'HTTP {response.status_code}'
            }
            
        except Exception as e:
            return {
                'site': site_name,
                'success': False,
                'error': str(e)
            }

    def comprehensive_test(self, query: str = "python developer", location: str = "Berlin") -> Dict:
        """Comprehensive testing of all sites"""
        print("🔍 Starting comprehensive testing...")
        
        results = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'query': query,
            'location': location,
            'site_availability': {},
            'search_functionality': {},
            'summary': {
                'total_sites': len(self.test_sites),
                'available_sites': 0,
                'working_search': 0,
                'blocked_sites': 0
            }
        }
        
        # Тестуємо доступність сайтів
        print("📡 Testing site availability...")
        for site_name in self.test_sites.keys():
            site_test = self.test_site_availability(site_name)
            results['site_availability'][site_name] = site_test
             
            if site_test['available']:
                results['summary']['available_sites'] += 1
            if site_test['blocked']:
                results['summary']['blocked_sites'] += 1
                
            time.sleep(1)
        
        # Тестуємо функціональність пошуку
        print("🔎 Testing search functionality...")
        for site_name in self.test_sites.keys():
            if results['site_availability'][site_name]['available']:
                search_test = self.test_search_functionality(site_name, query, location)
                results['search_functionality'][site_name] = search_test
                
                if search_test['success'] and search_test['has_job_content']:
                    results['summary']['working_search'] += 1
                    
                time.sleep(2)
        
        return results
