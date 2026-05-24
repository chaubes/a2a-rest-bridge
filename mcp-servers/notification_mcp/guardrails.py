"""Guardrail checks for notification tools.

Rules:
  * ``channel`` must be one of {email, sms}.
  * ``message`` must be at most 1000 characters.
"""

from __future__ import annotations

from shared.guardrails import GuardrailReport

ALLOWED_CHANNELS = {"email", "sms"}
MESSAGE_MAX_LENGTH = 1000


def check_channel(report: GuardrailReport, channel: str) -> GuardrailReport:
    if isinstance(channel, str) and channel in ALLOWED_CHANNELS:
        report.add("channel_allowed", True, f"{channel} is supported")
    else:
        report.add(
            "channel_allowed",
            False,
            f"channel '{channel}' is not supported; allowed values are "
            f"{sorted(ALLOWED_CHANNELS)}",
        )
    return report


def check_message(report: GuardrailReport, message: str) -> GuardrailReport:
    if not isinstance(message, str):
        report.add("message_length", False, f"message must be text; got {message!r}")
    elif len(message) <= MESSAGE_MAX_LENGTH:
        report.add("message_length", True, f"{len(message)} chars (<= {MESSAGE_MAX_LENGTH})")
    else:
        report.add(
            "message_length",
            False,
            f"message is {len(message)} characters; the maximum is "
            f"{MESSAGE_MAX_LENGTH}",
        )
    return report


def check_send_notification(message: str, channel: str) -> GuardrailReport:
    report = GuardrailReport()
    check_channel(report, channel)
    check_message(report, message)
    return report
