from django.contrib.admin.apps import AdminConfig


class FitHubAdminConfig(AdminConfig):
    """Use our admin site, which rate limits the admin login."""

    default_site = 'core.admin_site.ThrottledAdminSite'
