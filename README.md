# Session 1 — Echo Bot · Quick Start

Starter kit for Session 1: stand up a FastAPI webhook so the bot **echoes** messages back on Facebook Messenger.

## Steps

1. **Unzip** and open the `session1_starter` folder in a terminal (PowerShell).

2. **Create & activate a venv** with Python **3.11 or 3.12** (NOT 3.13/3.14):
   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python --version            # must print 3.12.x (or 3.11.x)
   ```
   > If activation is blocked: run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then activate again.

3. **Create your `.env`** from the template, then fill in the tokens:
   ```powershell
   Copy-Item .env.example .env
   ```
   Open `.env` and set:
   - `FB_VERIFY_TOKEN=` any random string you make up (you'll type the same value in Meta)
   - `FB_PAGE_ACCESS_TOKEN=` your fanpage's Page Access Token

4. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

5. **Run the server + ngrok** (two separate terminals; activate the venv in the uvicorn one):
   ```powershell
   uvicorn app.main:app --reload
   ```
   ```powershell
   ngrok http 8000
   ```

6. **Configure the webhook in Meta** following `session1_setup_guide_en.html`:
   - Callback URL = `https://<your-ngrok-url>/webhook`  *(remember the `/webhook`)*
   - Verify token = the exact `FB_VERIFY_TOKEN` from `.env`
   - Subscribe the `messages` field

## Test
Send **"hello"** from the page admin account to your fanpage → the bot replies **"hello"**.

## Notes
- Every new terminal: **activate the venv first** (`.\.venv\Scripts\Activate.ps1`).
- Keep **both terminals** (uvicorn + ngrok) running the whole time.
- **Never** commit/share your `.env` — it holds secret tokens.
