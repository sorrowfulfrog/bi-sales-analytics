-- External-system landing tables and Power BI marts.
-- Secrets are never stored in PostgreSQL.

CREATE TABLE IF NOT EXISTS jira_issues (
    issue_key VARCHAR(50) PRIMARY KEY,
    project_key VARCHAR(50) NOT NULL,
    summary TEXT NOT NULL,
    issue_type VARCHAR(100),
    status VARCHAR(100),
    status_category VARCHAR(100),
    priority VARCHAR(100),
    assignee VARCHAR(255),
    reporter VARCHAR(255),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    resolved_at TIMESTAMPTZ,
    story_points NUMERIC(12, 2),
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_jira_issues_project
    ON jira_issues(project_key);

CREATE INDEX IF NOT EXISTS idx_jira_issues_status
    ON jira_issues(status_category);

CREATE INDEX IF NOT EXISTS idx_jira_issues_updated
    ON jira_issues(updated_at);

CREATE TABLE IF NOT EXISTS crm_deals (
    deal_id BIGINT PRIMARY KEY,
    title TEXT NOT NULL,
    stage_id VARCHAR(100),
    stage_semantic_id VARCHAR(10),
    category_id BIGINT,
    opportunity NUMERIC(18, 2),
    currency_id VARCHAR(10),
    assigned_by_id BIGINT,
    contact_id BIGINT,
    company_id BIGINT,
    source_id VARCHAR(100),
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    is_closed BOOLEAN NOT NULL DEFAULT FALSE,
    is_won BOOLEAN NOT NULL DEFAULT FALSE,
    loaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_crm_deals_stage
    ON crm_deals(stage_id);

CREATE INDEX IF NOT EXISTS idx_crm_deals_created
    ON crm_deals(created_at);

CREATE OR REPLACE VIEW jira_delivery_kpi AS
SELECT
    DATE_TRUNC('month', created_at)::DATE AS month,
    project_key,
    COUNT(*) AS issues_created,
    COUNT(*) FILTER (
        WHERE status_category = 'Done'
    ) AS issues_done,
    COUNT(*) FILTER (
        WHERE status_category <> 'Done'
    ) AS open_issues,
    ROUND(SUM(story_points), 2) AS story_points,
    ROUND(
        AVG(
            EXTRACT(EPOCH FROM (resolved_at - created_at)) / 86400
        ) FILTER (WHERE resolved_at IS NOT NULL)::NUMERIC,
        2
    ) AS average_cycle_days
FROM jira_issues
GROUP BY
    DATE_TRUNC('month', created_at)::DATE,
    project_key;

CREATE OR REPLACE VIEW crm_funnel_kpi AS
SELECT
    stage_id,
    stage_semantic_id,
    COUNT(*) AS deals_count,
    ROUND(SUM(COALESCE(opportunity, 0)), 2) AS pipeline_amount,
    COUNT(*) FILTER (WHERE is_won) AS won_deals,
    ROUND(
        SUM(COALESCE(opportunity, 0)) FILTER (WHERE is_won),
        2
    ) AS won_amount
FROM crm_deals
GROUP BY
    stage_id,
    stage_semantic_id;
