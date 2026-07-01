# Integrating Aegis with Your Infrastructure

Aegis acts as the central intelligence hub for your operations. It can receive data from external systems, pull data natively from Alibaba Cloud, and push alerts out to your team. 

This guide explains the three primary ways Aegis connects to your systems.

---

## 1. External Tools Push Data TO Aegis (Inbound Webhook)
*Use this when you want tools like Datadog, AWS CloudWatch, or Prometheus to trigger an Aegis investigation.*

**How it works**: Your existing monitoring tool detects an anomaly (e.g., a CPU spike) and sends an HTTP POST request to Aegis's public API endpoint.

**How to configure it**:
You **do not** need to add any URLs to Aegis's `.env` file for this. Aegis is simply listening.
Instead, you configure the webhook URL inside your **external tool's settings**:

1. Find your Aegis deployment URL. Depending on where Aegis is hosted:
   - **Local Development**: `http://localhost:8000/api/webhook/incident`
   - **Render / Cloud Deployment**: `https://<your-aegis-app>.onrender.com/api/webhook/incident`
2. Go to your external monitoring tool's Alert/Webhook configuration page.
3. Paste the Aegis Webhook URL.
4. Configure the payload to send JSON (e.g., `{"service": "payment", "cpu": 95}`).

When the external tool fires, the Aegis **Detective Agent** intercepts the webhook and immediately starts an investigation.

---

## 2. Aegis Pulls Data FROM Alibaba Cloud (Active Polling)
*Use this for native, "always-on" monitoring of Alibaba Cloud resources.*

**How it works**: Aegis uses the Alibaba Cloud SDK to actively poll CloudMonitor and Log Service (SLS) every 30 seconds. It detects anomalies automatically without waiting for an external system to push data.

**How to configure it**:
No webhook URLs are required for this method. You only need to provide your Alibaba Cloud credentials to Aegis.

Add the following to your `backend/.env` file:
```env
ALIBABA_CLOUD_ACCESS_KEY_ID=your_access_key
ALIBABA_CLOUD_ACCESS_KEY_SECRET=your_secret_key
ALIBABA_CLOUD_REGION=ap-southeast-1
```
*(See `architecture.md` for details on extending the polling logic to suit your specific SLS projects).*

---

## 3. Aegis Pushes Data TO External Tools (Outbound Webhooks)
*Use this to receive human-readable alerts in Slack, Microsoft Teams, or Jira when Aegis detects and diagnoses an incident.*

**How it works**: After Aegis resolves an incident, the **Reporter Agent** formats a summary and sends an outbound JSON payload to your team's communication channel.

**How to configure it (Slack Example)**:
1. Go to [https://api.slack.com/apps](https://api.slack.com/apps) and create a new App ("From Scratch").
2. Enable **Incoming Webhooks** in the app settings.
3. Click **Add New Webhook to Workspace** and authorize it for your desired channel (e.g., `#incidents`).
4. Copy the generated Webhook URL (it will look like `https://hooks.slack.com/services/T...`).
5. Open your `backend/.env` file and add the URL:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR_WORKSPACE/YOUR_CHANNEL/YOUR_SECRET
```

Aegis will now automatically post detailed incident reports to this Slack channel.

---

## Quick Reference Summary

| Integration Type | Scenario | What You Need | Where to Put It |
| :--- | :--- | :--- | :--- |
| **Inbound Webhook** | External tool (Datadog) tells Aegis about a problem. | Aegis's `/api/webhook/incident` URL | The **External Tool's** alert settings. |
| **Active Polling** | Aegis natively watches Alibaba Cloud. | Alibaba Cloud Access Keys | Aegis's `backend/.env` file. |
| **Outbound Webhook** | Aegis sends a report to your team. | Slack Incoming Webhook URL | Aegis's `backend/.env` file (`SLACK_WEBHOOK_URL`). |

---

### Verifying the Setup Without External Tools

If you want to test Aegis immediately without setting up external webhooks or Alibaba Cloud polling:
1. Ensure your `QWEN_API_KEY` and `DATABASE_URL` are set in `.env`.
2. Open the Aegis Dashboard.
3. Click the **"Simulate Incident"** button. This internally triggers the webhook endpoint, allowing you to watch the agent pipeline run in real-time.
