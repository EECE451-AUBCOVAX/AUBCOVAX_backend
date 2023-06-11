# AUBCOVAX API

## Dependencies
Kindly check [requirements.txt](requirements.txt)

## Setup
1. Clone the repository `git clone https://github.com/EECE451-AUBCOVAX/AUBCOVAX_backend.git`
2. Navigate to the repository folder `cd AUBCOVAX_backend`
3. Create and activate a virtual environment
   - Windows
      - `py -m venv .venv`
      - `.venv\scripts\activate`
   - macOS/Linux
      - `python3 -m venv .venv` 
      - `source .venv/bin/activate`
4. Install the dependencies `pip install -r requirements.txt`
5. The pdf service requries *PDFLatex* which you can get from https://www.latex-project.org/get/.
6. Run the app `flask run`

## Features
- Patient Registration
- User Authentication
- User Info Retrieval
- User Search by Phone Number
- Patient Dose Tracking
- Vaccination Certificate
- Appointment Booking
- Appointment Email Notification

## Technologies
- Python Flask
- PDFLatex
- GitHub Actions
- Microsoft Azure
    - App Service
    - SQL 

## Deployment
The web app was deployed to Azure App Service at this [link](https://aubcovax.azurewebsites.net/).

### Kindly check [this](https://github.com/EECE451-AUBCOVAX) for more information about the AUBCOVAX platform.
