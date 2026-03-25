# Reporter

Reporter is a Django-based application for data aggregation, visualization, and reporting of different TACC (Texas Advanced Computing Center) services. It provides comprehensive analytics and insights into service usage, user activity, and system performance across multiple platforms.

## Overview

Reporter collects, processes, and visualizes usage data from various TACC services, enabling administrators and stakeholders to understand service utilization, track user engagement, and make data-driven decisions. The application supports multiple services including JupyterHub, Tapis API platform, and Hazmapper, with an extensible architecture that allows for easy addition of new services.

## Features

- **Multi-Service Support**: Track and analyze usage across multiple TACC services from a single platform
- **Automated Data Collection**: Parse logs from NGINX, Splunk, and Elasticsearch to extract usage metrics
- **Interactive Dashboards**: Web-based dashboards for visualizing usage statistics and trends
- **Multi-Tenant Architecture**: Support for multiple tenants (e.g., DesignSafe, TACC) within each service
- **Automated Reporting**: Generate and send email reports with usage statistics
- **Authentication**: Tapis OAuth-based authentication for secure access
- **Real-Time Analytics**: Process and display up-to-date usage metrics
- **Extensible Design**: Easy to add new services and data sources

## Architecture

### Technology Stack

- **Framework**: Django 3.2
- **Database**: MySQL
- **Web Server**: Gunicorn
- **Authentication**: Tapis OAuth
- **Data Sources**: NGINX logs, Splunk, Elasticsearch
- **Deployment**: Docker and Docker Compose

### Project Structure

```
reporter/
├── src/
│   ├── reporter/
│   │   ├── apps/           # Django applications
│   │   │   ├── jupyterhub/ # JupyterHub analytics
│   │   │   ├── tapis/      # Tapis API analytics
│   │   │   ├── main/       # Main dashboard
│   │   │   └── tapisauth/  # Authentication
│   │   ├── parsers/        # Data parsing modules
│   │   ├── helpers/        # Utility functions
│   │   ├── configs/        # Configuration files
│   │   └── settings.py     # Django settings
│   ├── parse_logs.py       # Log parsing entry point
│   ├── send_email.py       # Email reporting entry point
│   └── manage.py           # Django management script
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Sub-Projects

Reporter consists of multiple Django apps, each focused on a specific service:

### JupyterHub
Analyzes NGINX log files to track user logins, file operations, and notebook creation events across multiple JupyterHub instances.

**Key Metrics:**
- User login sessions
- Notebook creation and access
- File operations and directory usage
- Multi-tenant analytics (DesignSafe, TACC)

See [apps/README.md](src/reporter/apps/README.md#jupyterhub) for more details.

### Tapis
Comprehensive analytics for the Tapis API platform, including job execution, authentication metrics, service usage, publications, and training events.

**Key Metrics:**
- Job execution statistics
- Authentication tokens and unique users
- API service call volumes
- Research publications and citations
- Training event attendance
- Science gateway information

See [apps/README.md](src/reporter/apps/README.md#tapis) for more details.

## Installation

### Prerequisites

- Python 3.10+
- Docker and Docker Compose (optional, for containerized deployment)
- Access to service logs (NGINX, Splunk, Elasticsearch)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd reporter
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Create a `.env` file with the following variables:
   ```env
   DJANGO_SECRET_KEY=your-secret-key
   DEBUG=True
   TENANT=your-tenant
   INSTANCE=your-instance
   METADATA_NAME=your-metadata-name

   # Database
   MYSQL_HOST=localhost
   MYSQL_USER=your-db-user
   MYSQL_PASS=your-db-password
   MYSQL_DB=reporter_db

   # Service tokens
   JUPYTERHUB_TOKEN=your-jupyterhub-token
   GITHUB_API_TOKEN=your-github-token
   TAPIS_SERVICE_TOKEN=your-tapis-token

   # External services
   ELASTIC_HOST=your-elasticsearch-host
   ELASTIC_USR=your-elasticsearch-user
   ELASTIC_PWD=your-elasticsearch-password

   SLACK_CHANNEL=your-slack-channel
   SLACK_USER=your-slack-user
   SLACK_URL=your-slack-webhook-url
   ```

5. **Set up the database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   python manage.py collectstatic
   ```

6. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## Configuration

### Service Configuration

Services and tenants are configured in `src/reporter/configs/services.py`. Each service can have multiple tenants with their own configuration:

```python
services = [
    {
        "name": "jupyterhub",
        "admins": ["admin1", "admin2"],
        "tenants": [
            {
                "name": "designsafe",
                "proper_name": "DesignSafe",
                "directories": ["CommunityData", "MyData", ...],
                "primary_receiver": "email@example.com",
                "recipients": ["email1@example.com", "email2@example.com"],
            },
            # ... more tenants
        ],
    },
    # ... more services
]
```

### Data Sources

Data is collected from various sources:

- **NGINX Logs**: JupyterHub access logs (gzipped)
- **Splunk**: Tapis and Hazmapper service logs
- **MySQL**: Direct database queries for Tapis job statistics
- **External APIs**: GitHub API for repository information

## Usage

### Parsing Logs

To parse logs for a specific service:

```bash
python parse_logs.py --service jupyterhub
```

To parse logs for all services:

```bash
python parse_logs.py
```

Optional arguments:
- `--start_date` / `-sd`: Start date for log parsing
- `--end_date` / `-ed`: End date for log parsing
- `--service` / `-sv`: Specific service to parse

### Sending Email Reports

To send email reports for a service and tenant:

```bash
python send_email.py <service> <tenant>
```

Example:
```bash
python send_email.py jupyterhub designsafe
```

### Accessing Dashboards

1. Navigate to the Reporter web interface
2. Authenticate using Tapis OAuth
3. Access service-specific dashboards:
   - JupyterHub: `/jupyterhub/`
   - Tapis: `/tapis/`

### Admin Interface

Access the Django admin panel at `/admin/` to:
- Manage services and tenants
- View and edit data models
- Configure service administrators
- Monitor parsing status

## Data Collection

### Log Parsing Process

1. **File Discovery**: Identify log files to parse (NGINX logs, Splunk exports)
2. **Status Tracking**: Check if files have already been parsed (stored in database)
3. **Parsing**: Extract relevant events and metrics using service-specific parsers
4. **Data Storage**: Store parsed data in MySQL database
5. **Status Update**: Mark files as successfully parsed or failed

### Parsers

Each service has a dedicated parser in `src/reporter/parsers/`:

- **JupyterHubUsage**: Parses NGINX logs to extract login events and file operations
- **TapisUsage**: Processes Splunk logs and database queries for Tapis metrics

## Development

### Code Style

The project uses:
- **Black**: Code formatting (line length: 88)
- **isort**: Import sorting (Django profile)
- **djlint**: Django template linting

### Adding a New Service

1. Create a new Django app in `src/reporter/apps/`
2. Define models in `models.py`
3. Create views and templates for the dashboard
4. Implement a parser in `src/reporter/parsers/`
5. Add URL routing in `src/reporter/urls.py`
6. Update service configuration in `src/reporter/configs/services.py`
7. Add the app to `INSTALLED_APPS` in `settings.py`

See the existing services (JupyterHub, Tapis, Hazmapper) for examples.

## Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

## Support

For issues, questions, or contributions, please open an issue on the repository or contact the development team.

## Acknowledgments

Built for the Texas Advanced Computing Center (TACC) to support service analytics and reporting across multiple research computing platforms.
