# Final Project: Develop an Advanced Feature and Finalize the Application

## Project Overview

This project is a **FastAPI-based web application** enhanced with a newly developed advanced feature — **User Profile & Password Management**.  
The application leverages **SQLAlchemy** for database management and follows best practices for backend, frontend, and testing workflows.

### New Feature Highlights
- **View & update profile details** (username, email).
- **Securely change passwords** with hashing.
- Integrated **form validation**, **database updates**, and **real-time UI feedback**.

### Tech Stack & Tools
- **FastAPI** for backend API development.
- **SQLAlchemy** for ORM and database management.
- **Docker** for containerized deployment.
- **GitHub Actions** for CI/CD automation.
- **Pytest** for unit, integration, and end-to-end testing.

### Key Improvements
- Fully integrated **Docker deployment**.
- Automated testing and build pipeline via **GitHub Actions**.
- Production-grade practices for **secure authentication**, **database migrations**, and **frontend-backend synchronization**.


---


## My DockerHub Image
[Visit the DockerHub Page](https://hub.docker.com/r/pruthvidholkia/is601_final_project)


---


## Update profile and password
![Github action](/static/image/update_user.png)


![Github action](/static/image/update_profile.png)

![Github action](/static/image/update_password.png)


---


## New calculation Feature "Power"

![Github action](/static/image/power_function.png)


---


## Running Tests Locally
```bash
git clone https://github.com/pruthvidholakia/is601_final_project
cd is601_final_project
python -m venv venv
source venv/bin/activate             
pip install -r requirements.txt

```


---


## Install Dependencies

```bash
pip install -r requirements.txt
```


## Run All Tests

```bash
pytest
```

## Build Docker Image

```bash
docker build -t <image-name> .
```

---


## Run Docker Container
```bash
docker run -it --rm <image-name>
```
