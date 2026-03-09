# Project Status Reports Dashboard

A comprehensive Python-based dashboard application built with **Streamlit** for tracking and managing project status reports, features, and delivery timelines across different project types (AI, RPA, Software Development, Innovation).

## Features

### Project Management
- ✅ **Add Projects**: Create new projects with name, type, start/end dates, and current progress
- ✏️ **Edit Projects**: Update project details including name, type, dates, and progress
- 🗑️ **Delete Projects**: Remove projects from the system
- 📊 **Automatic Targeted Progress**: System automatically calculates what the progress should be based on elapsed time between start and end dates
- 📈 **Progress Tracking**: Compare actual progress vs. targeted progress with visual charts
- 🎯 **Project Types**: Support for AI, RPA, Software Development, and Innovation projects

### Feature Management
- 📦 **Add Features**: Add product features to projects with delivery dates
- 🗓️ **Feature Status**: Track features as Pending, In Progress, Completed, or Blocked
- ⏰ **Delivery Tracking**: Monitor feature delivery dates and overdue alerts
- 📋 **Feature Overview**: View all features across projects with status breakdowns

### Analytics & Reporting
- 📅 **Timeline Tracking**: Monitor days remaining and project deadlines
- 🕒 **Task Updates Timeline**: Capture project/task status updates and track progress development over time
- 📊 **Summary Dashboard**: View statistics and performance metrics across all projects
- 🔬 **Advanced Analytics**: Risk assessment, health status, performance metrics
- 📈 **Predictive Analytics**: Project completion forecasting
- 📉 **Visual Charts**: Interactive Plotly charts for data visualization
- 💾 **Data Persistence**: SQLite database for reliable local storage

## Project Structure

```
├── app.py              # Main Streamlit application
├── database.py         # Database operations and utilities
├── requirements.txt    # Python dependencies
├── projects.db         # SQLite database (auto-generated)
└── README.md          # This file
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. Navigate to the project directory:
```bash
cd /path/to/project
```

2. Create a virtual environment (optional but recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the Streamlit server:
```bash
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`

## Usage

### Adding a Project
1. Use the **"Add/Edit Project"** section in the left sidebar
2. Enter the project name
3. Select the project type
4. Set start and end dates
5. Input current progress (0-100%)
6. Click **"Add Project"**

### Dashboard Features
- **Progress Comparison**: See side-by-side comparison of actual vs. targeted progress
- **Timeline Info**: View start date, end date, and days remaining
- **Project Status**: Easily identify projects that are on track or behind schedule
- **Summary Statistics**: 
  - Average current and targeted progress
  - Number of projects on track vs. behind schedule
  - Breakdown of projects by type

### Managing Projects
- View all projects in the main dashboard
- Click **Delete** button to remove a project
- All data is automatically saved to SQLite database

## Data Storage

Projects are stored in a local SQLite database (`projects.db`). The database includes:
- Project name
- Project type
- Start date
- End date
- Current progress percentage
- Creation timestamp

## How Targeted Progress is Calculated

The system automatically calculates what the progress **should be** based on:
- Current date
- Project start date
- Project end date

**Formula**: 
```
Targeted Progress = (Days Elapsed / Total Days) × 100%
```

For example, if a project runs from Jan 1 to Dec 31 (365 days), and today is Feb 1 (31 days in):
- Targeted Progress = (31 / 365) × 100 ≈ 8.5%

## Technology Stack

- **Frontend**: Streamlit
- **Backend**: Python
- **Database**: SQLite3
- **Data Processing**: Pandas
- **Date Handling**: Python datetime & python-dateutil

## Future Enhancements

- Export reports to PDF/Excel
- Team collaboration features
- Project templates
- Risk indicators
- Milestone tracking
- Email notifications for overdue projects
- Dark mode theme

## License

This project is open source and available for personal or commercial use.
