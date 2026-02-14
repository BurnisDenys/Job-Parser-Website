# ==================== database.py ====================
# This file handles all database operations
# Stores jobs and search history in SQLite

import sqlite3
import json


class JobDatabase:
    
    def __init__(self, db_path="jobs.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                company TEXT,
                location TEXT,
                salary TEXT,
                summary TEXT,
                link TEXT UNIQUE,
                source TEXT,
                parsed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT,
                location TEXT,
                sources TEXT,
                results_count INTEGER,
                search_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON jobs(source)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_location ON jobs(location)')
        
        conn.commit()
        conn.close()
    
    def save_jobs(self, jobs):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        saved_count = 0
        
        for job in jobs:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO jobs 
                    (title, company, location, salary, summary, link, source, parsed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job['title'],
                    job['company'],
                    job['location'],
                    job['salary'],
                    job['summary'],
                    job['link'],
                    job['source'],
                    job['parsed_at']
                ))
                if cursor.rowcount > 0:
                    saved_count += 1
            except:
                continue
        
        conn.commit()
        conn.close()
        return saved_count
    
    def get_all_jobs(self, limit=100, offset=0):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM jobs ORDER BY created_at DESC LIMIT ? OFFSET ?', (limit, offset))
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    def search_jobs(self, query="", location="", source="", min_salary=None):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        sql = "SELECT * FROM jobs WHERE 1=1"
        params = []
        
        if query:
            sql += " AND (title LIKE ? OR summary LIKE ?)"
            params.extend([f"%{query}%", f"%{query}%"])
        
        if location:
            sql += " AND location LIKE ?"
            params.append(f"%{location}%")
        
        if source:
            sql += " AND source = ?"
            params.append(source)
        
        sql += " ORDER BY created_at DESC LIMIT 200"
        
        cursor.execute(sql, params)
        jobs = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return jobs
    
    def get_statistics(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM jobs")
        total = cursor.fetchone()[0]
        
        cursor.execute('SELECT source, COUNT(*) as count FROM jobs GROUP BY source')
        by_source = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute('SELECT location, COUNT(*) as count FROM jobs GROUP BY location ORDER BY count DESC LIMIT 10')
        by_location = {row[0]: row[1] for row in cursor.fetchall()}
        
        conn.close()
        
        return {
            'total': total,
            'by_source': by_source,
            'by_location': by_location
        }
    
    def save_search_history(self, query, location, 
                           sources, results_count):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        sources_json = json.dumps(sources)
        
        cursor.execute('INSERT INTO search_history (query, location, sources, results_count) VALUES (?, ?, ?, ?)',
                      (query, location, sources_json, results_count))
        
        conn.commit()
        conn.close()
     
    def get_search_history(self, limit=20):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM search_history ORDER BY search_date DESC LIMIT ?', (limit,))
        
        history = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return history
    
    def clear_old_jobs(self, days=30):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM jobs WHERE created_at < datetime("now", "-" || ? || " days")', (days,))
        
        deleted = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        return deleted
