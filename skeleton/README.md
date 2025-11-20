# Agentic Assistance for Retail E-commerce

This project is a sophisticated, AI-powered creative shopping assistant designed for a retail e-commerce store, specifically in the crafting or DIY space. It provides users with a conversational interface to discover project ideas, get product recommendations, and receive a complete, purchasable bundle of items.

The application's core is an intelligent agent built with a Large Language Model (LLM) that not only assists customers but also implements key business logic. It strategically promotes less popular ("low-velocity") inventory by dynamically incorporating these items into project bundles and generating appealing, AI-written descriptions to enhance their value to the customer.

## Key Features

- **AI Conversational Assistant:** A friendly chatbot interface for users to discover trends and projects.
- **Intelligent Project Discovery:** Guides users from vague ideas (e.g., "winter crafts") to concrete projects.
- **Dynamic Product Bundling:** Assembles all required products for a project into a single, convenient bundle.
- **Strategic Inventory Optimization:** Intelligently includes and promotes low-velocity products to help balance inventory.
- **AI-Generated Content:** Automatically creates catchy descriptions for promoted items and refines project steps to be more engaging.
- **Transparent Thought Process:** The frontend visualizes the agent's reasoning and tool usage in real-time.

## Technology Stack

- **Backend:** Python, Flask, LangChain, Google Gemini (via `google-generativeai`)
- **Frontend:** React.js, CSS

## Project Structure

The project is organized into two main directories:

- **/frontend:** Contains the React application for the user interface.
- **/backend:** Contains the Flask server, the LangChain agent, and all related business logic.

## Setup and Installation

### Prerequisites

- Node.js and npm
- Python 3.8+ and pip

### 1. Backend Setup

First, set up and run the backend server.

```bash
# Navigate to the backend directory
cd backend

# Create and activate a Python virtual environment
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate

# Install the required dependencies
pip install -r requirements.txt
```

### 2. Frontend Setup

Next, set up the React frontend.

```bash
# Navigate to the frontend directory
cd frontend

# Install the required npm packages
npm install
```

## Configuration

The backend requires a Google Gemini API key to function.

1.  In the `/backend` directory, create a new file named `.env`.
2.  Add your API key to this file as follows:

    ```
    GOOGLE_API_KEY="YOUR_API_KEY_HERE"
    ```

    **Important:** The `.env` file is included in `.gitignore` and should **never** be committed to version control.

## Usage

To run the application, you need to start both the backend and frontend servers in separate terminals.

1.  **Run the Backend Server:**
    - In your first terminal, navigate to the `/backend` directory and run:
    ```bash
    python app.py
    ```
    The backend server will start on `http://localhost:5000`.

2.  **Run the Frontend Application:**
    - In your second terminal, navigate to the `/frontend` directory and run:
    ```bash
    npm start
    ```
    The React development server will start and automatically open `http://localhost:3000` in your web browser.

You can now interact with the agent through the web interface.
