# Minimal safety patch

This commit adds a minimal security/UX patch to the demo FastAPI app:

- Escape HTML when rendering user-supplied values to mitigate XSS (uses html.escape).
- Map lesson plan status text to CSS classes so UI reflects status (pending/approved/rejected).
- URL-encode query parameters used in RedirectResponse and example links to avoid broken/untrusted URLs.
- Add a tiny validation on submitted `week` to ensure >= 1.

This is a small, low-risk patch meant to be the minimal fix requested. For a more complete hardening and cleanup consider:

- Moving templates to Jinja2 templates (auto-escaping and cleaner views).
- Adding server-side URL validation for file_link and preventing javascript: URIs.
- Adding CSRF protection for forms.
- Using a database layer (SQLAlchemy) and migrations.
