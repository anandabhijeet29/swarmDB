# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**swarmDB** is a "Git for Data Agents" system built on Agentic Postgres. The project enables multi-agent workflows that process and merge data insights with full audit trails and provenance tracking.

### Core Architecture

The system uses PostgreSQL as the backbone for:
- **Data storage**: Raw review data
- **Agent outputs**: Individual agent analysis results  
- **Merged insights**: Consolidated findings from multiple agents
- **Audit logs**: Complete history of agent executions with fork tracking

Think of it as a version control system where:
- Agents are like "branches" processing data independently
- `run_id` acts as a commit identifier
- `fork_name` enables parallel processing paths
- Merging happens at the database level with provenance tracking

## Commands

### Database Setup

Start PostgreSQL container:
```bash
docker-compose up -d
```

Stop database:
```bash
docker-compose down
```

Remove all data (use with caution):
```bash
docker-compose down -v
```

### Database Operations

Test database connection:
```bash
python scripts/test_db_connection.py
```

Initialize schema:
```bash
psql -h localhost -p 5432 -U swarm_user -d swarm_main -f scripts/schema.sql
```

Connect to database directly:
```bash
psql -h localhost -p 5432 -U swarm_user -d swarm_main
# Password: swarm_pass
```

### Python Environment

Activate virtual environment:
```bash
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

## Database Schema

### Core Tables

**reviews**: Source data for agent processing
- `id` (TEXT): Unique review identifier
- `created_at` (timestamptz): When review was created
- `user_id`, `region`, `rating`, `text`: Review metadata and content

**agent_outputs**: Individual agent processing results
- `id` (UUID): Auto-generated output ID
- `run_id` (TEXT): Groups outputs from same execution
- `agent_name` (TEXT): Which agent produced this
- `record_refs` (JSONB): References to source review IDs
- `summary`, `details` (TEXT/JSONB): Agent's findings
- `created_at` (timestamptz): Processing timestamp

**merged_insights**: Consolidated multi-agent results
- `id` (UUID): Merged insight identifier
- `run_id` (TEXT): Associated execution run
- `agent_name` (TEXT): Agent that performed merge
- `merged_summary` (TEXT): Combined analysis
- `details` (JSONB): Structured merge results
- `provenance` (JSONB): Tracks which agent_outputs contributed
- `created_at` (timestamptz): Merge timestamp

**agent_audit**: Execution tracking and debugging
- `id` (UUID): Audit record identifier
- `run_id` (TEXT): Execution identifier
- `agent_name`, `fork_name` (TEXT): Agent and branch identifiers
- `log` (TEXT): Execution logs/errors
- `status` (TEXT): Success/failure/running state
- `started_at`, `finished_at` (timestamptz): Timing information

## Key Patterns

### Run IDs
Use `run_id` consistently to track related operations across tables. Think of it as a transaction or commit ID that ties together agent outputs, merges, and audit logs.

### JSONB Fields
The schema uses JSONB extensively for flexibility:
- `record_refs`: Array of review IDs that an agent analyzed
- `details`: Structured agent findings (sentiment, themes, recommendations)
- `provenance`: Tracking lineage of merged data (which agents, output IDs)

When querying, use PostgreSQL's JSONB operators:
```sql
-- Extract array elements
SELECT record_refs->0 FROM agent_outputs;

-- Filter by JSON property  
SELECT * FROM agent_outputs WHERE details->>'sentiment' = 'positive';

-- Check array containment
SELECT * FROM agent_outputs WHERE record_refs @> '["review_123"]';
```

### Temporal Tracking
All tables use `timestamptz` for proper timezone handling. Use `created_at`/`started_at`/`finished_at` to:
- Debug processing order
- Calculate agent performance
- Implement time-based queries

### Fork-Based Parallelism
The `fork_name` field in `agent_audit` enables:
- Testing different agent configurations in parallel
- A/B testing agent logic
- Rollback to specific forks

## Development Notes

### Environment Variables
Connection details are in `.env` - **never commit real API keys or passwords**. The current GEMINI_API_KEY in .env is a placeholder.

### Dependencies
Core stack:
- `psycopg[binary,pool]`: PostgreSQL adapter with connection pooling
- `sqlalchemy`: ORM if needed
- `pandas`: Data manipulation  
- `python-dotenv`: Environment variable management
- `rich`: Terminal formatting
- `openai`: LLM integration (despite name, used broadly)
- `streamlit`: Web UI framework (likely for visualization)

### Database Connection Pattern
The project uses environment variables for all database configuration. Always reference:
```python
DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
```
Never hardcode connection strings.

## Project Structure

```
swarmDB/
├── agents/          # Agent implementation (currently placeholder)
├── data/           # Data files (empty directory)  
├── scripts/        # Database utilities
│   ├── schema.sql  # Complete database schema
│   └── test_db_connection.py  # Connection verification
├── docker-compose.yml  # PostgreSQL service definition
├── requirements.txt    # Python dependencies
└── .env           # Configuration (not tracked in git)
```

## Common Tasks

### Adding a New Agent
1. Create agent implementation in `agents/` directory
2. Ensure agent writes to `agent_outputs` with proper `run_id`
3. Add audit logging to `agent_audit`
4. Use `record_refs` to track source data

### Querying Agent Results
```python
# Example pattern for retrieving agent outputs
import psycopg
from dotenv import load_dotenv
import os

load_dotenv()
conn_info = {
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

with psycopg.connect(**conn_info) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT agent_name, summary, details 
            FROM agent_outputs 
            WHERE run_id = %s
        """, (run_id,))
        results = cur.fetchall()
```

### Implementing Merges
When merging agent outputs:
1. Query relevant `agent_outputs` by `run_id`
2. Perform aggregation/consensus logic
3. Write to `merged_insights` with `provenance` JSONB tracking source `agent_outputs.id` values
4. Ensure `run_id` consistency for traceability
