# AI Job Application Agent

Automates job applications on **LinkedIn Easy Apply** and **Indeed Quick Apply**
with AI-generated, per-job cover letters via the Anthropic API.

---

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

Edit `config.json`:

- Add your **Anthropic API key** → `agent_settings.anthropic_api_key`  
  Get one at https://console.anthropic.com
- Add your **LinkedIn and Indeed login credentials**
- Update your **profile** (name, degree, skills, top project)
- Set your **resume_path** to a local PDF file
- Adjust `roles`, `locations`, and `max_applications_per_day` to your preference

### 3. Run

```bash
# Both platforms, default limit from config.json
python job_agent.py

# LinkedIn only, 10 applications
python job_agent.py --platform linkedin --limit 10

# Indeed only
python job_agent.py --platform indeed

# Dry run — preview without submitting
python job_agent.py --dry-run
```

---

## Files

| File | Purpose |
|------|---------|
| `job_agent.py` | Main orchestrator — run this |
| `linkedin_agent.py` | LinkedIn Easy Apply automation |
| `indeed_agent.py` | Indeed Quick Apply automation |
| `anthropic_helper.py` | Cover letter + job scoring via Claude API |
| `tracker.py` | CSV logging and summary reporting |
| `config.json` | All settings and credentials |
| `applications.csv` | Auto-created — full application log |
| `agent.log` | Auto-created — session log |

---

## How it works

1. Logs into LinkedIn / Indeed using your credentials
2. Searches for each role × location combination from your config
3. Filters out jobs requiring senior experience or blacklisted companies
4. For each eligible Easy Apply job, calls the Anthropic API to write a
   tailored cover letter referencing the specific company and job description
5. Fills in the application form (name, phone, resume upload, cover letter)
6. Submits and logs the result to `applications.csv`

---

## Tips for freshers

- **Set `headless: false`** while testing so you can watch and intervene if
  needed (e.g. CAPTCHA, 2FA)
- **Start with `--dry-run`** to verify everything works before live submissions
- **Keep `max_applications_per_day` at 20–30** — too many flags your account
- **LinkedIn Easy Apply** and **Indeed Quick Apply** have the highest success
  rates; other platforms usually require full manual form filling
- **Update `top_project`** in config.json with your strongest GitHub project
  — the AI uses it to write a convincing, specific cover letter
- Run once per day, ideally in the morning (jobs posted overnight)

---

## Limitations & notes

- LinkedIn and Indeed occasionally update their HTML structure; if the agent
  stops working, inspect the page and update the CSS selectors in the agents
- CAPTCHA / 2FA steps require manual completion — the agent pauses and waits
- The agent only applies to Easy Apply / Quick Apply jobs (no external ATS forms)
- Your credentials are stored locally in `config.json` — never commit this file to Git
- Add `config.json` and `applications.csv` to `.gitignore`

---

## .gitignore (add this)

```
config.json
applications.csv
agent.log
resume.pdf
__pycache__/
*.pyc
```
