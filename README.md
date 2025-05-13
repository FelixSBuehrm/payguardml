# Findec

Findec is an intelligent SAP invoice analysis tool that uses SBERT and LLM models to identify potential duplicate invoices.

**Prerequisites:**

*   Access to a Gemini API key

**1. Clone the Repository (if you haven't already):**

```bash
git clone https://github.com/FelixSBuehrm/payguardml.git
cd payguardml
```

**2. Setup Backend:**

*   **Create `.env` file:**
    Navigate to the `backend/` directory and create a file named `.env`. Add your Gemini API key to it:
    ```
    # payguardml/backend/.env
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY_HERE"
    ```
*   **Install Python Dependencies:**
    It's highly recommended to use a virtual environment.
    ```bash
    cd backend # if not already there
    python3 -m venv venv
    source venv/bin/activate  # On macOS/Linux
    # venv\Scripts\activate    # On Windows

    # Navigate to the content directory to install requirements
    cd ../content
    pip install -r requirements.txt
    cd ../backend # Go back to backend directory
    ```

**3. Setup Frontend (Electron App):**

*   **Install Node.js Dependencies:**
    Navigate to the project root directory (`payguardml/`) if you aren't already there.
    ```bash
    npm install
    ```

**4. Running the Application Locally:**

*   From the project root directory (`payguardml/`):
    ```bash
    npm start
    ```
    This will launch the Findec Electron application.

**5. Building the Application Locally:**

*   Ensure all dependencies are installed (`npm install`).
*   From the project root directory (`payguardml/`):

    *   **To build for your current platform (e.g., macOS):**
        ```bash
        npm run dist
        ```
        Alternatively, for specific platforms:
    *   **For macOS (creates .dmg and .zip):**
        ```bash
        npm run dist:mac-arm
        or 
        npm run dist:mac-intel
        ```
    *   **For Windows (creates NSIS installer and .zip):**
        (Requires a Windows environment or appropriate cross-compilation setup)
        ```bash
        npm run dist:win
        # or
        npm run dist:win-x64
        ```
    *   The distributable files will be located in the `dist/` directory.
