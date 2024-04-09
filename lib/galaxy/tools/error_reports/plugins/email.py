"""The module describes the ``email`` error plugin."""

import logging

from galaxy.tools.errors import EmailErrorReporter
from galaxy.util import (
    string_as_bool,
    unicodify,
)
from . import ErrorPlugin

log = logging.getLogger(__name__)


class EmailPlugin(ErrorPlugin):
    """Send error report as an email"""

    plugin_type = "email"

    def __init__(self, **kwargs):
        self.app = kwargs["app"]
        self.redact_user_details_in_bugreport = self.app.config.redact_user_details_in_bugreport
        self.verbose = string_as_bool(kwargs.get("verbose", True))
        self.user_submission = string_as_bool(kwargs.get("user_submission", True))

    def submit_report(self, dataset, job, tool, **kwargs):
        """Send report as an email"""
        data_uid = None
        try:
            report_type = kwargs.get("report_type")
            transcript = kwargs.get("transcript")
            if report_type == "dataset":
                data_uid = dataset.id
                user = job.get_user()
            elif report_type == "tool":
                data_uid = dataset
                user = kwargs.get("user")

            error_reporter = EmailErrorReporter(data_uid, self.app, report_type)
            error_reporter.send_report(
                user=user,
                email=kwargs.get("email", None),
                message=kwargs.get("message", None),
                report_type=report_type,
                tool=tool,
                transcript=transcript,
                redact_user_details_in_bugreport=self.redact_user_details_in_bugreport,
            )
            return ("Your error report has been sent", "success")
        except Exception as e:
            return (f"An error occurred sending the report by email: {unicodify(e)}", "danger")


__all__ = ("EmailPlugin",)
