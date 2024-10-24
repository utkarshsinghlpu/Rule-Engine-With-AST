# Rule-Engine-with-AST
A simple Flask-based rule engine application(Simple UI, API and Backend, Data) to determine user eligibility based on attributes like age, department, income, spend etc.The system can use Abstract Syntax Tree (AST) to represent conditional rules and allow for dynamic creation,combination, and modification of these rules.
![Screenshot 2024-10-24 230227](https://github.com/user-attachments/assets/1c1dcc2d-f322-4380-a919-313270ae5153)



## Features

- Add new rules to the database.
- Evaluate rules against provided data.
- Combine multiple rules using AND/OR operators.
- Fetch and display existing rules.

## Prerequisites

- Python 3.8 or higher
- `pip` (Python package installer)

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/utkarshsinghlpu/Rule-Engine-with-AST
   cd flask-rule-engine

2. **Install the required packages:**
   
   ```bash
   pip install -r requirements.txt

## Run the application:

  ```bash
   python app.py
