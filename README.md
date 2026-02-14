# Job Parser

Web application for searching jobs from Indeed, StepStone & LinkedIn with SQLite database storage.

## 👇DEMO LINK:
https://job-parser-website-2.onrender.com


## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
python main.py
```

Open browser: http://localhost:8000

## 📊 Data Storage

### SQLite Database (`jobs.db`)

The application uses **SQLite** - a lightweight, file-based relational database that requires no separate server installation.

#### Database Schema:

**jobs** table:
- `id` - Primary key (auto-increment)
- `title` - Job title
- `company` - Company name
- `location` - Job location
- `salary` - Salary information
- `summary` - Job description
- `link` - URL to job posting (UNIQUE)
- `source` - Job board source (Indeed/StepStone/LinkedIn)
- `parsed_at` - When job was parsed
- `created_at` - When record was created

**search_history** table:
- `id` - Primary key
- `query` - Search query
- `location` - Search location
- `sources` - JSON array of sources
- `results_count` - Number of results found
- `search_date` - Timestamp

#### Storage Features:
- ✅ **Automatic creation** - Database created on first run
- ✅ **Duplicate prevention** - UNIQUE constraint on job links
- ✅ **Indexed searches** - Fast queries by source and location
- ✅ **Persistent storage** - Data survives server restarts
- ✅ **No external dependencies** - SQLite built into Python
- ✅ **Portable** - Single `jobs.db` file contains all data

#### Data Management:
```python
# View all jobs
GET /api/jobs?limit=50&offset=0

# Get statistics
GET /api/statistics

# View search history
GET /api/search-history

# Delete old jobs (30+ days)
DELETE /api/jobs/old?days=30
```

## 🔧 Features

- **Real-time parsing** from 3 job boards
- **Smart filtering** by salary and experience level
- **Link validation** - checks if job postings are accessible
- **Automatic testing** - validates site availability before parsing
- **Search history** - tracks all searches
- **Statistics** - jobs by source and location

## 📁 Project Structure

```
parser/
├── main.py          # FastAPI server
├── parser.py        # Job parsing logic
├── database.py      # SQLite operations
├── site_tester.py   # Site availability testing
├── index.html       # Web interface
├── requirements.txt # Python dependencies
├── start.bat        # Windows startup script
└── jobs.db          # SQLite database (auto-created)
```

## 🛠 Technology Stack

**Backend:**
- FastAPI - Modern Python web framework
- SQLite - Embedded relational database
- BeautifulSoup4 - HTML parsing
- Requests - HTTP client

**Frontend:**
- HTML5 + CSS3
- Vanilla JavaScript
- Responsive design

**Data Storage:**
- SQLite 3.x
- File-based storage
- ACID compliant
- No configuration required

## 📝 API Endpoints

- `GET /` - Home page
- `POST /api/search` - Search jobs
- `GET /api/jobs` - Get saved jobs
- `GET /api/statistics` - Get statistics
- `GET /api/search-history` - Get search history
- `DELETE /api/jobs/old` - Delete old jobs

## 🔍 Search Parameters

- **Job Title** - Search query (e.g., "python developer")
- **Location** - City (Berlin, Munich, Hamburg, etc.)
- **Min Salary** - Minimum salary in EUR
- **Experience** - All Levels / Junior / Senior
- **Pages** - Number of pages to parse (1-5)
- **Sources** - Indeed.de, StepStone.de, LinkedIn

## 💾 Database Backup

To backup your data, simply copy the `jobs.db` file:

```bash
# Backup
copy jobs.db jobs_backup.db

# Restore
copy jobs_backup.db jobs.db
```

## 🔒 Data Privacy

- All data stored locally in `jobs.db`
- No external database connections
- No data sent to third parties
- Full control over your data

## 📊 Performance
 
- **Storage**: ~1KB per job record
- **Speed**: Instant local queries
- **Capacity**: Millions of records supported
- **Indexing**: Optimized for fast searches

## 🐛 Troubleshooting

**Database locked error:**
- Close other applications accessing `jobs.db`
- Restart the server

**Database corrupted:**
- Delete `jobs.db` (will be recreated)
- Restore from backup if available

## 📄 License

MIT License - Free to use and modify





