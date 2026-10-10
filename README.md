# AI Fitness Tracker

A full-stack fitness tracking application built to help users record workouts, monitor training progress, and receive AI-powered workout recommendations.

## Features

- **Workout Management:** Add, edit, and delete workout entries.
- **Workout History:** View past workouts, exercises, and training dates.
- **Progress Analytics:** Track workout counts, sets, reps, and training volume.
- **Progress Charts:** Visualize performance by exercise over time.
- **Workout Calendar:** View training activity by date.
- **AI Workout Recommendations:** Get workout insights and training suggestions.

## Technologies Used

- **Backend:** Python, FastAPI
- **Database:** PostgreSQL, SQLAlchemy
- **Frontend:** HTML, CSS, JavaScript
- **Data Visualization:** Chart.js
- **AI Integration:** OpenAI API

## What I Learned

- Building API endpoints with FastAPI
- Connecting a Python application to PostgreSQL
- Implementing create, read, update, and delete (CRUD) operations
- Creating interactive charts and workout analytics
- Integrating AI-powered recommendations
- Managing project files and version control with Git and GitHub

## Running the Project Locally

1. Clone the repository:
   
     git clone https://github.com/kani4prezzzz/ai-fitness-tracker.git
     cd ai-fitness-tracker
   
2. Create and activate a Python virtual environment.

3. Install the dependencies:
     pip install -r requirements.txt

4. Configure your PostgreSQL database and required environment variables.

5. Start the application:
     uvicorn main:app --reload

6. Open http://127.0.0.1:8000 in your browser.

## Security

Store API keys and other secrets in environment variables. Never commit your `.env` file or private credentials to GitHub.

## Author

Kani Smith
