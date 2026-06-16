"""
anthropic_helper.py
───────────────────
Generates tailored cover letters using the Anthropic API (claude-sonnet-4-6).
Each letter is customised to the specific job description and company.
"""

import anthropic


def generate_cover_letter(api_key: str, profile: dict, job: dict) -> str:
    """
    Generate a tailored cover letter for a specific job.

    Args:
        api_key:  Anthropic API key
        profile:  Candidate profile dict from config.json
        job:      Job dict with keys: title, company, description, location, url

    Returns:
        Cover letter as a plain string (ready to paste into application forms)
    """
    client = anthropic.Anthropic(api_key=api_key)

    job_title       = job.get("title", "the role")
    company         = job.get("company", "your company")
    job_description = job.get("description", "")[:2000]   # trim to keep tokens low
    location        = job.get("location", "")

    skills_str  = ", ".join(profile.get("skills", [])[:8])
    name        = profile.get("full_name", "Candidate")
    degree      = profile.get("degree", "")
    university  = profile.get("university", "")
    project     = profile.get("top_project", "")
    summary     = profile.get("summary", "")
    grad_year   = profile.get("graduation_year", "")

    prompt = f"""You are writing a job application cover letter on behalf of this candidate.

CANDIDATE PROFILE
─────────────────
Name:        {name}
Degree:      {degree} — {university} ({grad_year})
Skills:      {skills_str}
Top project: {project}
Summary:     {summary}

JOB DETAILS
───────────
Role:        {job_title}
Company:     {company}
Location:    {location}
Description: {job_description}

INSTRUCTIONS
────────────
Write a cover letter that is:
• 3 short paragraphs, max 200 words total
• Specific to this company and role — reference the company name and at least one detail from the job description
• Confident but not arrogant — fresher applying with strong project experience
• Opening line: bold and specific, NOT "I am writing to apply for..."
• Middle paragraph: 1-2 concrete skills or projects that match this role
• Closing: clear call to action asking for an interview
• Tone: professional, direct, warm
• No generic filler phrases like "I am a quick learner" or "team player"
• Do NOT include subject line, date, address headers, or signature — just the 3 paragraphs

Output ONLY the cover letter text. Nothing else."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )

    return message.content[0].text.strip()


def score_job_match(api_key: str, profile: dict, job: dict) -> int:
    """
    Score how well a job matches the candidate profile (0-100).
    Used to prioritise which jobs to apply to first.
    """
    client = anthropic.Anthropic(api_key=api_key)

    skills_str  = ", ".join(profile.get("skills", []))
    description = job.get("description", "")[:1000]
    title       = job.get("title", "")

    prompt = f"""Rate how well this job matches this candidate on a scale of 0-100.

Candidate skills: {skills_str}
Candidate level: fresher / 0 years experience

Job title: {title}
Job description excerpt: {description}

Rules:
- 80-100: Strong match — role is explicitly entry-level or intern, skills align well
- 60-79:  Good match — entry-level role, some skill overlap
- 40-59:  Partial match — transferable skills but some gaps
- 0-39:   Poor match — requires significant experience or unrelated field

Respond with ONLY a single integer (0-100). No explanation."""

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=10,
        messages=[{"role": "user", "content": prompt}],
    )

    try:
        return int(message.content[0].text.strip())
    except ValueError:
        return 50   # default to neutral if parsing fails
