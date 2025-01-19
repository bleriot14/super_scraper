 # SuperScraper

A powerful web scraping API built with FastAPI and Selenium for automated menu data extraction and processing.

## Features

- FastAPI-based REST API
- Selenium-powered web scraping
- Automated menu data extraction
- Configurable workflows
- Logging and monitoring with Prometheus integration
- Docker support for easy deployment

## Prerequisites

- Python 3.8+
- Docker and Docker Compose (for containerized deployment)
- Chrome/Chromium browser (for Selenium)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/superscraper.git
cd superscraper
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

### Local Development

1. Start the FastAPI server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

2. Access the API documentation at:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

### Using Docker

1. Build and start the containers:
```bash
docker-compose up --build
```

## Project Structure

```
superscraper/
├── app/
│   ├── core/           # Core functionality and configurations
│   ├── routers/        # API route definitions
│   ├── tasks/          # Scraping tasks and workflows
│   └── main.py         # Application entry point
├── docker-compose.yml  # Docker composition configuration
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Configuration

The application can be configured through environment variables or configuration files. Key configurations include:

- Server port (default: 8001)
- Logging levels and destinations
- Prometheus metrics configuration

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.