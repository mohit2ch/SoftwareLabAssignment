# SoftwareLabAssignment

## Automatic collection and filtering of Proxy server addresses 

This project automates the collection and filtering of proxy server addresses using Python. It performs web scraping to gather proxy addresses from multiple online sources, then tests each proxy to verify its functionality and measures key metrics such as response time. The project filters out non-working or slow proxies to ensure reliability. Finally, it presents the validated proxy list along with detailed statistics like location and response time through a user friendly Flask web interface.

## Project Architecture

![project-architecture-image](./project_architecture.png)

## File-wise description

### Backend

**main.py**: This file initializes a Flask web application with CORS that exposes API endpoints to control and retrieve status from a ProxyScheduler and its list of validated proxy items.

**models.py**: This file defines a data model class ProxyItem to structure proxy server information (IP, port, protocol, validation status, etc.) and provides methods for string representation and uniqueness checks.

**proxy_scheduler.py**: This file defines the ProxyScheduler class, which uses background threading to periodically fetch, validate, and store a collection of ProxyItem objects.

**proxy_validator.py**: This file contains functions to parallelly validate a list of proxy servers using a ThreadPoolExecutor, checking their connectivity, response time, location, against specified URLs using the requests library.

**providers directory**: This directory contains web scraping files that scrape various free proxy address websites using beautiful-soup.

### Frontend
