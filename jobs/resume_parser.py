import re


def parse_resume(file_obj):
    """Parse resume file and extract email, phone, skills"""
    try:
        # Read file content
        content = file_obj.read().decode("utf-8", errors="ignore")

        # Extract email
        email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
        emails = re.findall(email_pattern, content)
        email = emails[0] if emails else None

        # Extract phone
        phone_pattern = r"\d{3}[-.\s]?\d{3}[-.\s]?\d{4}"
        phones = re.findall(phone_pattern, content)
        phone = phones[0] if phones else None

        # Extract skills
        skills_list = [
            "python",
            "javascript",
            "react",
            "django",
            "java",
            "sql",
            "postgresql",
            "mongodb",
            "aws",
            "docker",
            "html",
            "css",
            "git",
        ]
        found_skills = [
            skill for skill in skills_list if skill.lower() in content.lower()
        ]

        return {"email": email, "phone": phone, "skills": found_skills}
    except Exception as e:
        print(f"Parse error: {e}")
        return {"email": None, "phone": None, "skills": []}
