# Student Expense Tracker

## Overview

The Student Expense Tracker is a Python application designed to help students monitor their daily spending and understand their purchasing behaviour.

Users can enter an expense amount, a short description, and their allocated budget. The system uses an AI API to analyse each expense and categorise it. The AI-generated information is then processed by business rules to identify potential overspending and provide spending insights.

## Problem Statement

Students often spend money on food, transportation, entertainment, education, and other daily expenses. However, they may not consistently track their spending or realise when they are spending too much in a particular category.

This application aims to provide students with a simple way to record expenses and receive an overview of their spending habits.

## Target Users

* Polytechnic and university students
* Students who want to monitor their daily spending
* Students with a fixed budget who want to avoid overspending

## Key Features

* Record daily expenses
* Enter allocated budgets
* Use AI to automatically categorise expenses
* Analyse purchasing behaviour
* Identify potential overspending
* Compare expected and actual usage
* Store expense records for future reference
* View previous expense records

## System Architecture

The application follows a four-manager architecture:

```text
User Input
    ↓
IO Manager
    ↓
AI Manager
    ↓
Logic Manager
    ↓
Data Manager
```

### IO Manager

Responsible for interaction between the user and the system.

* Collects user input
* Validates user input
* Displays records and summaries
* Handles all `print()` statements

### AI Manager

Responsible for AI processing.

* Builds prompts from expense records
* Sends every expense record to the AI API
* Parses the AI response
* Validates the AI response structure
* Handles API failures without crashing the application

### Logic Manager

Responsible for applying the application's business rules to the AI-generated information.

Examples include:

* Checking spending against the allocated budget
* Identifying potential overspending
* Processing AI-generated expense categories
* Evaluating purchase behaviour
* Generating an outcome or recommendation

### Data Manager

Responsible for storing and retrieving application data.

* Saves processed records to JSON or CSV
* Loads existing records when the application starts
* Provides filtering and query functions
* Handles missing or corrupted data files

## User Inputs

The application accepts information such as:

| Input            | Example               |
| ---------------- | --------------------- |
| Expense Amount   | `8.50`                |
| Description      | `Lunch at McDonald's` |
| Allocated Budget | `300`                 |
| Date             | `2026-09-22`          |

## AI Processing

Every expense record is passed through the AI Manager.

The AI analyses the expense description and returns structured information such as:

* Expense category
* Purchase type
* Expected usage
* Spending insight

The application validates the AI response before passing it to the Logic Manager.

## Business Rules

The system applies predefined rules to the AI-generated output.

Examples include:

* Expense amount must be positive
* Allocated budget must be positive
* Expense description cannot be empty
* AI-generated categories must match the predefined categories
* Spending is checked against the allocated budget
* Multiple AI output fields may be used together to determine the final outcome

## Data Storage

Expense records and their AI-generated results are stored using JSON or CSV files.

Example:

```text
data/
└── expenses.json
└── expenses.csv
```

Data is loaded when the application starts so that previous records can be accessed across different runs.

## Project Structure

```text
LABP1Team1_project/
│
├── main.py
├── io_manager.py
├── ai_manager.py
├── logic_manager.py
└── data_manager.py
│
├── data/
│   └── expenses.json
│
├── tests/
│   └── test_script.py
│
├── .env
├── .gitignore
├── .dockerignore
├── Dockerfile
├── requirements.txt
└── README.md
```

## Running the Project

### Run locally

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
python main.py
```

## Running with Docker

**First time** (build the image and create the container):

```bash
docker build -t student-expense-tracker .
docker run -it --name expense-tracker --env-file .env -v ./data:/app/data student-expense-tracker
```

**Running it again** (reuses the same container):

```bash
docker start -ai expense-tracker
```

**After changing the code** (rebuild the image and recreate the container):

```bash
docker build -t student-expense-tracker .
docker rm expense-tracker
docker run -it --name expense-tracker --env-file .env -v ./data:/app/data student-expense-tracker
```

What the options do:

* `-it` is required because the app reads keyboard input
* `--name expense-tracker` gives the container a fixed name so it can be restarted with `docker start`
* `--env-file .env` passes the API key in at runtime (it is never copied into the image)
* `-v ./data:/app/data` keeps `data/spending.json` on your machine, so expenses are not lost when the container is stopped or removed
* `docker start -ai` reattaches your terminal (`-a`) and keyboard input (`-i`); the `.env` and volume settings are remembered from `docker run`

## Project Requirements

The project follows the requirements provided for the team project:

* Four-manager architecture
* Procedural Python only
* AI API processing for every record
* Structured AI responses
* JSON or CSV persistence
* Docker support
* Git-based development and history
