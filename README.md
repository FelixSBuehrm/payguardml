# Findec

Findec is an intelligent SAP invoice analysis tool that uses SBERT and LLM models to identify potential duplicate invoices.

## Local Development

This guide provides concise steps to run, test, and build the Findec application locally.

**Prerequisites:**

*   Node.js and npm (Node Package Manager)
*   Python 3.x and pip
*   Access to a Gemini API key

**1. Clone the Repository (if you haven't already):**

```bash
git clone <your-repository-url>
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
*   **Ensure SBERT Model and Threshold are Present:**
    *   The SBERT model should be in `content/invoice_sbert/`.
    *   The threshold file should be `content/best_threshold.txt`.

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

**5. Testing the Application:**

*   **Backend Python Scripts:**
    1.  Ensure your virtual environment is activated.
    2.  Prepare a sample CSV file (e.g., `val_pairs.csv` or your own test data).
    3.  Navigate to the `backend/` directory.
    4.  Run `main.py` with your input CSV:
        ```bash
        # Make sure you are in the payguardml/backend/ directory
        # Adjust the path to your input CSV as needed.
        # For example, if val_pairs.csv is in the root:
        python main.py --input ../val_pairs.csv
        ```
    5.  Check the console for logs and the `output/run_<timestamp>/` directory for the SBERT temporary CSV and the final JSON output.

*   **Electron App (End-to-End):**
    1.  Run the app using `npm start`.
    2.  Use the UI to drag & drop or browse for your input CSV file.
    3.  Click "Process Invoices".
    4.  Observe the logs in the app's UI.
    5.  Check Electron's developer console (usually toggled via View > Toggle Developer Tools in the app menu) for logs from `main.js` and `renderer.js`.
    6.  Verify that the `processing-complete` message appears with the correct JSON output path.
    7.  Test the "Open Output Folder" button.

**6. Building the Application Locally:**

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

**Important Notes:**

*   **Python Path:** The Electron app attempts to use `python3` (or `python` on Windows) from the system's PATH. If you have multiple Python versions or use a specific environment not on the PATH, the Python backend might not run correctly when launched from the packaged Electron app. For production builds distributed to other users, consider bundling a Python runtime.
*   **Icons:** Replace placeholder icons in `build/` (`icon.icns`, `icon.ico`) and `app/logo_placeholder.png` with your actual application graphics for a professional look. The `.icns` file for macOS should be a multi-resolution icon.
*   **API Key:** The `GEMINI_API_KEY` in `backend/.env` is crucial for the LLM classification part. This file is gitignored and should not be committed to your repository.
