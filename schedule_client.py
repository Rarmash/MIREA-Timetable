from datetime import date

import requests

from options import SCHEDULE_API_TIMEOUT, SCHEDULE_API_URL


class ScheduleAPIError(Exception):
    pass


class ScheduleClient:
    def get_schedule(self, group, date_from: date, date_to: date):
        try:
            response = requests.get(
                f"{SCHEDULE_API_URL}/api/schedule/by-name",
                params={
                    "query": group,
                    "target": 1,
                    "date_from": date_from.isoformat(),
                    "date_to": date_to.isoformat(),
                },
                timeout=SCHEDULE_API_TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as exc:
            raise ScheduleAPIError from exc
        lessons = data.get("lessons")
        if not isinstance(lessons, list):
            raise ScheduleAPIError("Invalid schedule response")
        return sorted(lessons, key=lambda item: (item.get("date", ""), item.get("time_start", "")))
