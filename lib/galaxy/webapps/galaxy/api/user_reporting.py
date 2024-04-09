# """
# API controller providing functionality for users to self-report errors they experience 
# """

from . import (
    depends,
    DependsOnTrans,
    Router,
)
from fastapi import (
    Body,
)
import json
from typing_extensions import Annotated

from galaxy.config import GalaxyAppConfiguration
from galaxy.managers.context import ProvidesUserContext
from galaxy.schema.schema import (
    UserReportingErrorSummary,
    UserReportingErrorPayload,
)

ReportErrorBody = Body(default=..., title="Report error", description="The values to report an Error")

router = Router(tags=["user-reporting"])

@router.cbv
class UserSelfReportingApi:
    config: GalaxyAppConfiguration = depends(GalaxyAppConfiguration)

    @router.post("/api/user-reporting/error", public=True)
    def email_report(
        self,
        payload: Annotated[UserReportingErrorPayload, ReportErrorBody],
        trans: ProvidesUserContext = DependsOnTrans,
    ) -> UserReportingErrorSummary:
        transcriptJson = json.loads(payload.transcript)
        self.app = trans.app
        user = trans.get_user()
        self.tool = trans.app.toolbox.get_tool(transcriptJson["tool_id"], tool_version=transcriptJson["tool_version"])
        messages = trans.app.error_reports.default_error_plugin.submit_report(
            dataset=None,
            job=None,
            tool=self.tool,
            user=user,
            user_submission=True,
            report_type="tool",
            email=payload.email,
            message=payload.message,
            transcript=payload.transcript,
        )
        return UserReportingErrorSummary(messages=messages)
