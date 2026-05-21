# ── Log Analytics Workspace ───────────────────────────────────
resource "azurerm_log_analytics_workspace" "velibdata" {
  name                = "log-velibdata"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "PerGB2018"
  retention_in_days   = 90   # CdC §4.3.5 — 90 jours rétention
}

# ── Application Insights ──────────────────────────────────────
resource "azurerm_application_insights" "velibdata" {
  name                = "appi-velibdata"
  location            = var.location
  resource_group_name = var.resource_group_name
  workspace_id        = azurerm_log_analytics_workspace.velibdata.id
  application_type    = "other"
}

# ── Action Group: alerts → email ──────────────────────────────
resource "azurerm_monitor_action_group" "team" {
  name                = "ag-velibdata-team"
  resource_group_name = var.resource_group_name
  short_name          = "velibdata"

  email_receiver {
    name                    = "team-lead"
    email_address           = var.alert_email
    use_common_alert_schema = true
  }
}

# ── Alert: no messages in Event Hubs for 2+ min (ingestion lag)
# CdC §4.3.2 — latence ingestion > 120s → CRITIQUE ─────────────
resource "azurerm_monitor_metric_alert" "ingestion_lag" {
  name                = "alert-ingestion-no-messages"
  resource_group_name = var.resource_group_name
  scopes              = [var.eventhub_namespace_id]
  severity            = 0
  frequency           = "PT5M"
  window_size         = "PT15M"
  description         = "CRITIQUE: No messages received in Event Hubs for 5 minutes — ingestion pipeline may be down"

  criteria {
    metric_namespace = "Microsoft.EventHub/namespaces"
    metric_name      = "IncomingMessages"
    aggregation      = "Total"
    operator         = "LessThan"
    threshold        = 1
  }

  action {
    action_group_id = azurerm_monitor_action_group.team.id
  }
}

# ── Alert: high error rate in Event Hubs > 5%
# CdC §4.3.2 — taux d'erreur API > 5% → CRITIQUE ──────────────
resource "azurerm_monitor_metric_alert" "error_rate" {
  name                = "alert-eventhub-errors"
  resource_group_name = var.resource_group_name
  scopes              = [var.eventhub_namespace_id]
  severity            = 0
  frequency           = "PT5M"
  window_size         = "PT15M"
  description         = "CRITIQUE: Event Hubs error rate exceeds 5%"

  criteria {
    metric_namespace = "Microsoft.EventHub/namespaces"
    metric_name      = "ServerErrors"
    aggregation      = "Total"
    operator         = "GreaterThan"
    threshold        = 5
  }

  action {
    action_group_id = azurerm_monitor_action_group.team.id
  }
}

# ── Budget: $100 Azure for Students — alerts at 50% and 80%
# CdC §13.2 — dépassement budget risque ÉLEVÉ ─────────────────
resource "azurerm_consumption_budget_resource_group" "velibdata" {
  name              = "budget-velibdata"
  resource_group_id = var.resource_group_id
  amount            = var.budget_amount
  time_grain        = "Monthly"

  time_period {
    start_date = var.budget_start_date
  }

  notification {
    enabled        = true
    threshold      = 50
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = [var.alert_email]
  }

  notification {
    enabled        = true
    threshold      = 80
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = [var.alert_email]
  }

  notification {
    enabled        = true
    threshold      = 95
    operator       = "GreaterThan"
    threshold_type = "Actual"
    contact_emails = [var.alert_email]
  }
}
