# Agentic Assistance for Retail E-commerce (Backstage Template)

This repository contains both the source code for an AI-powered creative shopping assistant and the necessary files to use it as a [Backstage.io](https://backstage.io/) software template.

## 1. Project Overview

This application is a sophisticated, AI-powered creative shopping assistant designed for a retail e-commerce store, specifically in the crafting or DIY space. It provides users with a conversational interface to discover project ideas, get product recommendations, and receive a complete, purchasable bundle of items.

The application's core is an intelligent agent built with a Large Language Model (LLM) that not only assists customers but also implements key business logic. It strategically promotes less popular ("low-velocity") inventory by dynamically incorporating these items into project bundles and generating appealing, AI-written descriptions to enhance their value to the customer. This turns a simple chatbot into a smart sales and inventory optimization tool.

### Key Features

- **AI Conversational Assistant:** A friendly chatbot interface for users to discover trends and projects.
- **Intelligent Project Discovery:** Guides users from vague ideas (e.g., "winter crafts") to concrete projects.
- **Dynamic Product Bundling:** Assembles all required products for a project into a single, convenient bundle.
- **Strategic Inventory Optimization:** Intelligently includes and promotes low-velocity products to help balance inventory.
- **AI-Generated Content:** Automatically creates catchy descriptions for promoted items and refines project steps to be more engaging.
- **Transparent Thought Process:** The frontend visualizes the agent's reasoning and tool usage in real-time.

### Technology Stack

- **Backend:** Python, Flask, LangChain, Google Gemini (`google-generativeai`)
- **Frontend:** React.js, CSS
- **DevOps:** Backstage.io for cataloging and scaffolding

## 2. Repository Structure

This repository is a monorepo with a specific structure required for Backstage templates.

- `/template.yaml`: The Backstage Scaffolder file that defines the template's UI and steps.
- `/catalog-info.yaml`: The Backstage Catalog file that registers this template as a component.
- `/skeleton/`: **This directory contains the entire source code for the application.** When you generate a new project from the template, the contents of this folder are used as the base.
  - `/skeleton/backend/`: The Python Flask backend.
  - `/skeleton/frontend/`: The React frontend.
  - `/skeleton/README.md`: The detailed README for a *generated* project.

## 3. How to Use as a Backstage Template

1.  **Register in Backstage:** Add this repository's URL to your Backstage instance via `Create -> Register Existing Component`.
2.  **Use the Template:** Once registered, find the "Agentic E-commerce Assistant Template" in your "Create" page.
3.  **Fill and Generate:** Fill out the form with your new component's name, owner, and repository location. Backstage will create a new repository containing the code from the `/skeleton` directory.

## 4. How to Run This Project Locally

All commands for local development should be run relative to the `/skeleton` directory.

### Prerequisites

- Node.js and npm
- Python 3.8+ and pip

### Step 1: Backend Setup

First, set up and run the backend server.

```bash
# Navigate to the backend directory
cd skeleton/backend

# Create and activate a Python virtual environment
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt
```

### Step 2: Backend Configuration

The backend requires a Google Gemini API key.

1.  In the `skeleton/backend` directory, create a new file named `.env`.
2.  Add your API key to this file:
    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```
    **Important:** The `.env` file is included in `.gitignore` and should **never** be committed to version control.

### Step 3: Frontend Setup

Next, set up the React frontend.

```bash
# Navigate to the frontend directory from the root
cd skeleton/frontend

# Install the required npm packages
npm install
```

### Step 4: Run the Application

You need two separate terminals to run the application.

1.  **Run the Backend Server:**
    - In your first terminal, from the `skeleton/backend` directory, run:
    ```bash
    python app.py
    ```
    The backend server will start on `http://localhost:5000`.

2.  **Run the Frontend Application:**
    - In your second terminal, from the `skeleton/frontend` directory, run:
    ```bash
    npm start
    ```
    The React development server will start and automatically open `http://localhost:3000` in your web browser.

You can now interact with the agent through the web interface.