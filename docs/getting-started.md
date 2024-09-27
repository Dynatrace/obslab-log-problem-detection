# Getting Started

## Dynatrace Environment

You must have access to a Dynatrace SaaS environment. If you need one, ([sign up here](https://dt-url.net/trial){target="_blank"})

Save the Dynatrace environment URL:

* Without the trailing slash
* Without `.apps.` in the URL

The generic format is:

```
https://<EnvironmentID>.<Environment>.<URL>
```

For example:
```
https://abc12345.live.dynatrace.com
```

## Custom Runbook

!!! info
    As the developer responsible for the cartservice, if problems occur, you're the best person to know how to resolve the issue.

    To help your colleagues, you have prebuilt a notebook which will be useful as a runbook if / when problems occur.

    You want to make this notebook automatically available whenever problems with the `cartservice` occur.

Download the file [Redis Troubleshooting.json]() and save to your computer.

In Dynatrace:

* Press `ctrl + k`. Search for `notebooks`
* Open the app and find the `Upload` button at the top of the page
* Upload the JSON file you previously downloaded

![upload button](images/notebook-upload-button.png)

* Make a note of the notebook ID from the URL bar

![notebook ID](images/notebook-id.png)

### Create API Token

In Dynatrace:

* Press `ctrl + k`. Search for `access tokens`.
* Create a new access token with the following permissions:
    * `logs.ingest`
    * `metrics.ingest`
    * `openTelemetryTrace.ingest`
    * `events.ingest`

#### API Token Permissions Explained
* `logs.ingest`, `metrics.ingest` and `openTelemetryTrace.ingest` are required to send the relevant telemetry data into Dynatrace
* `events.ingest` is required to send the `CUSTOM_CONFIGURATION` event into Dynatrace

## Start Demo

Click this button to open the demo environment. This will open in a new tab.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/dynatrace/obslab-log-problem-detection){target="_blank"}

<div class="grid cards" markdown>
- [Click Here to Continue :octicons-arrow-right-24:](installation-explained.md)
</div>