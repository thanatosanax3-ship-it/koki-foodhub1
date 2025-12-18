Deploy instructions for Render (auto-deploy via GitHub Actions)

1) Add two repository secrets in GitHub:
   - RENDER_API_KEY: create an API key in Render (Account -> API Keys) and paste it here
   - RENDER_SERVICE_ID: get your service ID from Render (Settings -> Service Details) and paste it here

2) After adding both secrets, pushing to `main` will run the `Deploy to Render` workflow which triggers a new deploy.

3) If you prefer manual deploy instead:
   - Go to Render dashboard -> select your Web Service -> Manual Deploy -> choose latest commit -> Deploy

Notes:
- The Action uses Render's API to create a deploy so the service redeploys without entering the Render console.
- If you prefer, I can open a PR with this workflow and the instructions instead of pushing directly to `main`.
