"""Python Playwright UI audit toolkit."""


def audit_site(*args, **kwargs):
    from .auditor import audit_site as run_audit_site

    return run_audit_site(*args, **kwargs)

__all__ = ["audit_site"]
__version__ = "1.0.0"
