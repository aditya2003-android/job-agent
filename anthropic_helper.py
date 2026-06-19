from anthropic import Anthropic


def generate_cover_letter(api_key: str, profile: dict, job: dict) -> str:
    if not api_key:
        return "Missing API key"

    client = Anthropic(api_key=api_key)

    prompt = f"""
Write a 3 paragraph cover letter (max 200 words).

Candidate: {profile}
Job: {job}

Rules:
- Mention company name
- Match skills
- No generic text
"""

    try:
        res = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=400,
            messages=[{"role": "user", "content": prompt}],
        )
        return res.content[0].text.strip()
    except Exception as e:
        return f"ERROR: {e}"


def score_job_match(api_key: str, profile: dict, job: dict) -> int:
    client = Anthropic(api_key=api_key)

    prompt = f"""
Rate job match 0-100

Profile: {profile}
Job: {job}

Only number.
"""

    try:
        res = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}],
        )
        return int(res.content[0].text.strip())
    except:
        return 50
