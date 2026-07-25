from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from typing import Any

import psycopg
import requests
from dotenv import load_dotenv


JIRA_FIELDS = [
    "summary",
    "project",
    "issuetype",
    "status",
    "priority",
    "assignee",
    "reporter",
    "created",
    "updated",
    "resolutiondate",
]

BITRIX_DEAL_FIELDS = [
    "ID",
    "TITLE",
    "STAGE_ID",
    "STAGE_SEMANTIC_ID",
    "CATEGORY_ID",
    "OPPORTUNITY",
    "CURRENCY_ID",
    "ASSIGNED_BY_ID",
    "CONTACT_ID",
    "COMPANY_ID",
    "SOURCE_ID",
    "DATE_CREATE",
    "DATE_MODIFY",
    "CLOSEDATE",
    "CLOSED",
]


def required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def database_connection() -> psycopg.Connection[Any]:
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5434"),
        dbname=os.getenv("POSTGRES_DB", "bi_database"),
        user=os.getenv("POSTGRES_USER", "bi_user"),
        password=required_env("POSTGRES_PASSWORD"),
    )


def display_name(value: dict[str, Any] | None) -> str | None:
    return value.get("displayName") if value else None


def fetch_jira_issues() -> list[tuple[Any, ...]]:
    base_url = required_env("JIRA_BASE_URL").rstrip("/")
    email = required_env("JIRA_EMAIL")
    token = required_env("JIRA_API_TOKEN")
    story_points_field = os.getenv(
        "JIRA_STORY_POINTS_FIELD",
        "customfield_10016",
    )
    fields = [*JIRA_FIELDS, story_points_field]
    jql = os.getenv("JIRA_JQL", "ORDER BY updated ASC")
    next_page_token: str | None = None
    rows: list[tuple[Any, ...]] = []

    with requests.Session() as session:
        session.auth = (email, token)
        session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

        while True:
            payload: dict[str, Any] = {
                "jql": jql,
                "fields": fields,
                "maxResults": 100,
            }
            if next_page_token:
                payload["nextPageToken"] = next_page_token

            response = session.post(
                f"{base_url}/rest/api/3/search/jql",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            page = response.json()

            for issue in page.get("issues", []):
                issue_fields = issue.get("fields", {})
                status = issue_fields.get("status") or {}
                status_category = status.get("statusCategory") or {}
                project = issue_fields.get("project") or {}
                issue_type = issue_fields.get("issuetype") or {}
                priority = issue_fields.get("priority") or {}

                rows.append(
                    (
                        issue.get("key"),
                        project.get("key"),
                        issue_fields.get("summary") or "",
                        issue_type.get("name"),
                        status.get("name"),
                        status_category.get("name"),
                        priority.get("name"),
                        display_name(issue_fields.get("assignee")),
                        display_name(issue_fields.get("reporter")),
                        issue_fields.get("created"),
                        issue_fields.get("updated"),
                        issue_fields.get("resolutiondate"),
                        issue_fields.get(story_points_field),
                    )
                )

            next_page_token = page.get("nextPageToken")
            if page.get("isLast") is True or not next_page_token:
                break

    return rows


def fetch_bitrix_deals() -> list[tuple[Any, ...]]:
    webhook_url = required_env("BITRIX24_WEBHOOK_URL").rstrip("/")
    endpoint = f"{webhook_url}/crm.deal.list.json"
    start = 0
    rows: list[tuple[Any, ...]] = []

    with requests.Session() as session:
        while True:
            payload: dict[str, Any] = {
                "order[ID]": "ASC",
                "start": start,
            }
            for index, field in enumerate(BITRIX_DEAL_FIELDS):
                payload[f"select[{index}]"] = field

            response = session.post(endpoint, data=payload, timeout=60)
            response.raise_for_status()
            page = response.json()
            if "error" in page:
                raise RuntimeError(
                    f"Bitrix24 API error: {page['error']} - "
                    f"{page.get('error_description', '')}"
                )

            for deal in page.get("result", []):
                semantic = deal.get("STAGE_SEMANTIC_ID")
                rows.append(
                    (
                        deal.get("ID"),
                        deal.get("TITLE") or "",
                        deal.get("STAGE_ID"),
                        semantic,
                        deal.get("CATEGORY_ID") or None,
                        deal.get("OPPORTUNITY") or 0,
                        deal.get("CURRENCY_ID"),
                        deal.get("ASSIGNED_BY_ID") or None,
                        deal.get("CONTACT_ID") or None,
                        deal.get("COMPANY_ID") or None,
                        deal.get("SOURCE_ID"),
                        deal.get("DATE_CREATE"),
                        deal.get("DATE_MODIFY"),
                        deal.get("CLOSEDATE") or None,
                        deal.get("CLOSED") == "Y",
                        semantic == "S",
                    )
                )

            next_start = page.get("next")
            if next_start is None:
                break
            start = int(next_start)

    return rows


def upsert_jira(
    connection: psycopg.Connection[Any],
    rows: Iterable[tuple[Any, ...]],
) -> int:
    data = list(rows)
    if not data:
        return 0

    statement = """
        INSERT INTO jira_issues (
            issue_key, project_key, summary, issue_type, status,
            status_category, priority, assignee, reporter, created_at,
            updated_at, resolved_at, story_points
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (issue_key) DO UPDATE SET
            project_key = EXCLUDED.project_key,
            summary = EXCLUDED.summary,
            issue_type = EXCLUDED.issue_type,
            status = EXCLUDED.status,
            status_category = EXCLUDED.status_category,
            priority = EXCLUDED.priority,
            assignee = EXCLUDED.assignee,
            reporter = EXCLUDED.reporter,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at,
            resolved_at = EXCLUDED.resolved_at,
            story_points = EXCLUDED.story_points,
            loaded_at = NOW()
    """
    with connection.cursor() as cursor:
        cursor.executemany(statement, data)
    return len(data)


def upsert_bitrix(
    connection: psycopg.Connection[Any],
    rows: Iterable[tuple[Any, ...]],
) -> int:
    data = list(rows)
    if not data:
        return 0

    statement = """
        INSERT INTO crm_deals (
            deal_id, title, stage_id, stage_semantic_id, category_id,
            opportunity, currency_id, assigned_by_id, contact_id,
            company_id, source_id, created_at, updated_at, closed_at,
            is_closed, is_won
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s
        )
        ON CONFLICT (deal_id) DO UPDATE SET
            title = EXCLUDED.title,
            stage_id = EXCLUDED.stage_id,
            stage_semantic_id = EXCLUDED.stage_semantic_id,
            category_id = EXCLUDED.category_id,
            opportunity = EXCLUDED.opportunity,
            currency_id = EXCLUDED.currency_id,
            assigned_by_id = EXCLUDED.assigned_by_id,
            contact_id = EXCLUDED.contact_id,
            company_id = EXCLUDED.company_id,
            source_id = EXCLUDED.source_id,
            created_at = EXCLUDED.created_at,
            updated_at = EXCLUDED.updated_at,
            closed_at = EXCLUDED.closed_at,
            is_closed = EXCLUDED.is_closed,
            is_won = EXCLUDED.is_won,
            loaded_at = NOW()
    """
    with connection.cursor() as cursor:
        cursor.executemany(statement, data)
    return len(data)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Load Jira Cloud and Bitrix24 data into PostgreSQL."
    )
    parser.add_argument(
        "--source",
        choices=("jira", "bitrix", "all"),
        default="all",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch data but do not write to PostgreSQL.",
    )
    args = parser.parse_args()

    load_dotenv()
    jira_rows: list[tuple[Any, ...]] = []
    bitrix_rows: list[tuple[Any, ...]] = []

    if args.source in {"jira", "all"}:
        jira_rows = fetch_jira_issues()
        print(f"Jira issues fetched: {len(jira_rows):,}")

    if args.source in {"bitrix", "all"}:
        bitrix_rows = fetch_bitrix_deals()
        print(f"Bitrix24 deals fetched: {len(bitrix_rows):,}")

    if args.dry_run:
        print("Dry run complete; PostgreSQL was not changed.")
        return

    with database_connection() as connection:
        jira_count = upsert_jira(connection, jira_rows)
        bitrix_count = upsert_bitrix(connection, bitrix_rows)
        connection.commit()

    print(f"Jira issues upserted: {jira_count:,}")
    print(f"Bitrix24 deals upserted: {bitrix_count:,}")


if __name__ == "__main__":
    main()
