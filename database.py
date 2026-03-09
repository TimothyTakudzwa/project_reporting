import sqlite3
import os
from datetime import datetime, timedelta
import pandas as pd

DB_PATH = "projects.db"

def init_db():
    """Initialize the database with projects and features tables."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create projects table
    c.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            project_type TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            current_progress INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create features table
    c.execute('''
        CREATE TABLE IF NOT EXISTS features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            feature_name TEXT NOT NULL,
            delivery_date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )
    ''')
    
    # Create user adoption tracking table (for specific apps)
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_adoptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            app_name TEXT NOT NULL,
            num_users INTEGER NOT NULL,
            adoption_date TEXT NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(app_name, adoption_date)
        )
    ''')

    # Create project updates tracking table
    c.execute('''
        CREATE TABLE IF NOT EXISTS project_updates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            task_name TEXT NOT NULL,
            update_text TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'In Progress',
            progress_percent INTEGER NOT NULL DEFAULT 0,
            update_date TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()

def add_project(name, project_type, start_date, end_date, current_progress):
    """Add a new project to the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO projects (name, project_type, start_date, end_date, current_progress)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, project_type, start_date, end_date, current_progress))
    conn.commit()
    conn.close()

def get_all_projects():
    """Retrieve all projects from the database."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM projects", conn)
    conn.close()
    return df

def delete_project(project_id):
    """Delete a project from the database."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()
    conn.close()

def update_project(project_id, name, project_type, start_date, end_date, current_progress):
    """Update an existing project."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE projects 
        SET name = ?, project_type = ?, start_date = ?, end_date = ?, current_progress = ?
        WHERE id = ?
    ''', (name, project_type, start_date, end_date, current_progress, project_id))
    conn.commit()
    conn.close()

def calculate_targeted_progress(start_date, end_date):
    """Calculate the targeted progress based on current date between start and end dates."""
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    today = datetime.now()
    
    if today < start:
        return 0
    if today > end:
        return 100
    
    total_duration = (end - start).days
    elapsed_duration = (today - start).days
    
    if total_duration == 0:
        return 100
    
    targeted_progress = int((elapsed_duration / total_duration) * 100)
    return min(targeted_progress, 100)

# Feature management functions
def add_feature(project_id, feature_name, delivery_date, status='Pending'):
    """Add a feature to a project."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO features (project_id, feature_name, delivery_date, status)
        VALUES (?, ?, ?, ?)
    ''', (project_id, feature_name, delivery_date, status))
    conn.commit()
    conn.close()

def get_project_features(project_id):
    """Get all features for a specific project."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM features WHERE project_id = ? ORDER BY delivery_date",
        conn,
        params=(project_id,)
    )
    conn.close()
    return df

def update_feature(feature_id, feature_name, delivery_date, status):
    """Update a feature."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE features 
        SET feature_name = ?, delivery_date = ?, status = ?
        WHERE id = ?
    ''', (feature_name, delivery_date, status, feature_id))
    conn.commit()
    conn.close()

def delete_feature(feature_id):
    """Delete a feature."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM features WHERE id = ?", (feature_id,))
    conn.commit()
    conn.close()

def get_project_by_id(project_id):
    """Get a single project by ID."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM projects WHERE id = ?", conn, params=(project_id,))
    conn.close()
    return df.iloc[0] if len(df) > 0 else None
# User Adoption Tracking Functions
def add_adoption(app_name, num_users, adoption_date, notes=''):
    """Add a new user adoption record for an app."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO user_adoptions (app_name, num_users, adoption_date, notes)
            VALUES (?, ?, ?, ?)
        ''', (app_name, num_users, adoption_date, notes))
        conn.commit()
    except sqlite3.IntegrityError:
        # Update if record already exists for this app on this date
        c.execute('''
            UPDATE user_adoptions
            SET num_users = ?, notes = ?
            WHERE app_name = ? AND adoption_date = ?
        ''', (num_users, notes, app_name, adoption_date))
        conn.commit()
    conn.close()

def get_all_adoptions():
    """Retrieve all user adoption records."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM user_adoptions ORDER BY adoption_date DESC", conn)
    conn.close()
    return df

def get_adoption_by_date(adoption_date):
    """Get all adoption records for a specific date."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM user_adoptions WHERE adoption_date = ? ORDER BY app_name",
        conn,
        params=(adoption_date,)
    )
    conn.close()
    return df

def get_app_adoption_history(app_name):
    """Get adoption history for a specific app."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(
        "SELECT * FROM user_adoptions WHERE app_name = ? ORDER BY adoption_date",
        conn,
        params=(app_name,)
    )
    conn.close()
    return df

def get_adoption_by_id(adoption_id):
    """Get a single adoption record by ID."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM user_adoptions WHERE id = ?", conn, params=(adoption_id,))
    conn.close()
    return df.iloc[0] if len(df) > 0 else None

def update_adoption(adoption_id, app_name, num_users, adoption_date, notes=''):
    """Update an adoption record."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE user_adoptions
        SET app_name = ?, num_users = ?, adoption_date = ?, notes = ?
        WHERE id = ?
    ''', (app_name, num_users, adoption_date, notes, adoption_id))
    conn.commit()
    conn.close()

def delete_adoption(adoption_id):
    """Delete an adoption record."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DELETE FROM user_adoptions WHERE id = ?", (adoption_id,))
    conn.commit()
    conn.close()


def add_project_update(project_id, task_name, update_text, status, progress_percent, update_date):
    """Add a project/task status update."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO project_updates (project_id, task_name, update_text, status, progress_percent, update_date)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (project_id, task_name, update_text, status, progress_percent, update_date))
    conn.commit()
    conn.close()


def get_project_updates(project_id=None):
    """Retrieve project updates, optionally filtered by project."""
    conn = sqlite3.connect(DB_PATH)

    if project_id is None:
        df = pd.read_sql_query(
            '''
            SELECT pu.*, p.name as project_name
            FROM project_updates pu
            JOIN projects p ON pu.project_id = p.id
            ORDER BY pu.update_date DESC, pu.created_at DESC
            ''',
            conn
        )
    else:
        df = pd.read_sql_query(
            '''
            SELECT pu.*, p.name as project_name
            FROM project_updates pu
            JOIN projects p ON pu.project_id = p.id
            WHERE pu.project_id = ?
            ORDER BY pu.update_date DESC, pu.created_at DESC
            ''',
            conn,
            params=(project_id,)
        )

    conn.close()
    return df