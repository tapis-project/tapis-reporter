# Reporter Apps

This directory contains the sub-projects for the Reporter application, each focused on aggregating, analyzing, and reporting usage data for different TACC services.

## Overview

The Reporter application provides data aggregation, visualization, and reporting capabilities for various TACC services. Each sub-project (app) is responsible for collecting, processing, and presenting usage metrics for its respective service.

## Sub-Projects

### JupyterHub

The JupyterHub app analyzes NGINX log files from JupyterHub instances to track user activity, including logins and file operations.

**Key Features:**
- **Log Parsing**: Parses gzipped NGINX log files to extract user activity
- **Login Tracking**: Monitors user login events across multiple tenants
- **File Operations**: Tracks file creation and access patterns
- **Notebook Detection**: Uses regex patterns to detect when new Jupyter notebooks are created
- **Multi-Tenant Support**: Supports multiple tenants including DesignSafe and TACC

**Models:**
- `FileLog`: Tracks file operations (created, opened files) with user, tenant, date/time, filepath, and action
- `LoginLog`: Records user login events by tenant, user, date, and time
- `ParsedNginxFile`: Manages parsing status of NGINX log files (queued, opened, succeeded, failed)

**Usage:**
The app processes NGINX logs to identify:
- User login sessions
- Notebook creation events (POST requests to `/api/contents/` followed by GET requests)
- File access patterns and directory usage

For detailed information about notebook creation detection logic, see [jupyterhub/README.md](jupyterhub/README.md).

---

### Hazmapper

The Hazmapper app tracks usage data for the Hazmapper application, a mapping tool used for hazard visualization and analysis.

**Key Features:**
- **Usage Tracking**: Monitors user interactions with Hazmapper maps
- **Elasticsearch Integration**: Queries DesignSafe Elasticsearch to collect usage data
- **Map Analytics**: Tracks map access, publication status, and project associations
- **User Statistics**: Provides overview of total users, maps accessed, and projects

**Models:**
- `HazmapperData`: Stores usage events with user, date, time, application, map name, project, and publication status (is_public, published)

**Data Collected:**
- Number of times Hazmapper was called
- Number of unique maps accessed
- Total number of users
- Total number of projects
- Map publication status and visibility settings

---

### Tapis

The Tapis app provides comprehensive tracking and reporting for the Tapis API platform, a distributed computational research infrastructure.

**Key Features:**
- **Jobs Analytics**: Tracks job execution data including daily averages, totals, and smart scheduling usage
- **Authentication Metrics**: Monitors token generation and unique user counts
- **Service Usage**: Tracks API call volumes across different Tapis services (jobs, streams, files, etc.)
- **Multi-Tenant Support**: Supports multiple tenants (tacc, designsafe, dev.develop, etc.)
- **Publications Tracking**: Maintains records of research papers and publications related to Tapis
- **Training Events**: Tracks training sessions, forums, and attendance
- **Gateway Information**: Manages data about science gateways using Tapis

**Models:**
- `JobsData`: Stores job statistics per tenant (average daily jobs, total jobs, smart scheduling usage)
- `TenantJobsData`: Daily job counts per tenant and version (v2/v3)
- `TenantServiceUsage`: Service usage logs with date, time range, tenant, service, and call counts
- `TapisInfo`: Tenant-level metrics (number of tokens, unique users, containerized apps)
- `TapisCallData`: Service call data by date, tenant, and service
- `Paper`: Research publications and citations related to Tapis
- `Training`: Training event records with name, forum, date, and attendance

**Data Sources:**
- Splunk logs for service usage and API calls
- Database queries for job statistics
- External sources for publications and gateway information
- JSON data files for gateways, papers, and training events

**Analytics Provided:**
- Authentication statistics (tokens, unique users)
- Job execution metrics (daily averages, totals, scheduling preferences)
- Streams API usage
- Service-specific call volumes
- Publication and citation tracking
- Training event attendance

---

## Common Structure

Each app follows a standard Django app structure:

- `models.py`: Database models for storing usage data
- `views.py`: View functions for rendering dashboards and reports
- `urls.py`: URL routing configuration
- `admin.py`: Django admin interface configuration
- `templates/`: HTML templates for displaying data
- `static/`: CSS and other static files
- `migrations/`: Database migration files

## Data Collection

Each app uses parsers located in `src/reporter/parsers/` to collect and process raw data:

- **JupyterHub**: `JupyterHubUsage.py` - Parses NGINX log files
- **Hazmapper**: `HazmapperUsage.py` - Queries Elasticsearch
- **Tapis**: `TapisUsage.py` - Processes Splunk logs and database queries

## Authentication

All apps require user authentication. The `tapisauth` app provides Tapis OAuth-based authentication for accessing the Reporter dashboards.
