# Smart Classroom System - Deployment Guide

This guide details how to run, test, and deploy the Smart Classroom System project directly from **Visual Studio Code (VS Code)**.

---

## Part 1: Local Development & Setup

### 1. Open Project in VS Code
1. Launch VS Code.
2. Select **File > Open Folder...** and navigate to:
   `C:\Users\manas\.gemini\antigravity\scratch\smart-classroom`
3. Open a terminal inside VS Code: press **Ctrl + `** (backtick) or select **Terminal > New Terminal**.

### 2. Activate Virtual Environment & Run
The project already contains a pre-configured Python virtual environment (`venv`).
- **In PowerShell (VS Code default on Windows)**:
  ```powershell
  # If you get execution policy restrictions, run:
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
  
  # Activate venv
  .\venv\Scripts\Activate.ps1
  ```
- **In Git Bash or Command Prompt**:
  ```bash
  source venv/Scripts/activate # Git Bash
  venv\Scripts\activate.bat   # Command Prompt
  ```

Once activated, your terminal prompt will be prefixed with `(venv)`.

### 3. Run Seeder and Start Web App
1. Seed the local SQLite database with initial classrooms, teacher accounts, and dummy student rosters:
   ```bash
   python seed.py
   ```
2. Start the local server:
   ```bash
   python app.py
   ```
3. Open your browser and navigate to:
   `http://127.0.0.1:5000`

---

## Part 2: Push Your Code to GitHub

Cloud hosting platforms deploy applications by pulling code directly from a GitHub repository.

1. **Initialize Git Repository** (in the root folder `smart-classroom`):
   ```bash
   git init
   ```
2. **Stage and Commit all files**:
   ```bash
   git add .
   git commit -m "Initial commit: Smart Classroom System"
   ```
3. **Publish to GitHub**:
   - Go to [GitHub](https://github.com) and log in.
   - Click the **New** repository button.
   - Name it `smart-classroom` (leave it public, do **not** initialize with README, .gitignore, or license).
   - In VS Code, copy the commands from GitHub's instructions under "push an existing repository from the command line" and run them:
     ```bash
     git branch -M main
     git remote add origin https://github.com/YOUR_USERNAME/smart-classroom.git
     git push -u origin main
     ```

---

## Part 3: Provision a Free PostgreSQL Database

SQLite databases are stored as local files. When deployed to free hosting platforms (like Render or Railway), these files are erased whenever the server sleeps or restarts. To prevent attendance records from disappearing, we must connect a production database.

1. Go to [Neon.tech](https://neon.tech/) and sign up for a free account.
2. Create a new project named `smart-classroom`. Select **PostgreSQL 16** (or latest) and choose your nearest region.
3. In the Neon dashboard, copy your **Connection String** (it starts with `postgresql://...`). Make sure it is set to the **Pooled** connection or standard direct URI.
4. Keep this connection string safe. You will provide it to Render.

---

## Part 4: Deploy the Web App on Render

Render is a free-tier hosting platform that supports Flask applications natively.

### 1. Create a New Web Service on Render
1. Sign in to [Render](https://render.com/).
2. Click **New +** and select **Web Service**.
3. Link your GitHub account and choose the `smart-classroom` repository.

### 2. Configure Build & Start Settings
Set the following properties in the Render dashboard configuration page:
- **Name**: `smart-classroom-system` (or any custom name)
- **Environment / Runtime**: `Python`
- **Region**: Select the region closest to you
- **Branch**: `main`
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  gunicorn app:app
  ```

### 3. Add Environment Variables
Scroll down to the **Environment Variables** section and add the following:

| Key | Value | Description |
| :--- | :--- | :--- |
| `DATABASE_URL` | *Your Neon PostgreSQL connection string* | Links Render to the Postgres database |
| `SECRET_KEY` | *Generate a random secure string (e.g. `c1a2s3s4r5o6o7m`)* | Secures session cookies |
| `PYTHON_VERSION` | `3.14.2` | Matches local development environment |

### 4. Deploy and Initial Seed
1. Click **Deploy Web Service**.
2. Wait 2-3 minutes for the build logs to finish and display "Live".
3. **Database Migration:** Since the database tables are created automatically on startup by `init_db()` in `app.py`, they will be created in your Neon PostgreSQL database instantly when the server starts.
4. **Seed Database in Production:**
   If you want to pre-populate your live database with the default teacher and student accounts:
   - Go to the **Shell** tab in the Render sidebar (or run it via local CLI pointing to production Postgres).
   - In the Render web shell, run:
     ```bash
     python seed.py
     ```
   - This seeds your Neon Postgres database.

---

## Part 5: Verify Deployment

1. Once the service is marked "Live", click the unique URL provided by Render (e.g., `https://smart-classroom-system.onrender.com`).
2. Log in with the default credentials:
   - **Teacher**: username: `teacher` / password: `admin123`
   - **Student**: username: `alice` / password: `password123`
3. Test the features: mark attendance for today, upload lecture notes, and verify they persist when you log in as a student!
