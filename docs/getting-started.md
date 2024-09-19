# Getting Started

You must have the following to use this hands on demo.

* A Dynatrace environment ([sign up here](https://dt-url.net/trial){target="_blank"})
* A Dynatrace API token (see below)

Save the Dynatrace environment URL **without** the trailing slash and without the `.apps.` in the URL:

```
https://abc12345.live.dynatrace.com
```

### Create API Token

In Dynatrace:

* Press `ctrl + k`. Search for `access tokens`.
* Create a new access token with the following permissions:
    * `logs.ingest`
    * `events.ingest`
    * `settings.read`
    * `settings.write`

#### API Token Permissions Explained
* `logs.ingest` is required to send log entries into Dynatrace
* `events.ingest` is required to send the `CUSTOM_CONFIGURATION` event into Dynatrace
* `settings.read` and `settings.write` are required to create the custom `service` entity type

## Start Demo

Click this button to open the demo environment. This will open in a new tab.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/dynatrace/obslab-log-problem-detection){target="_blank"}

<div class="grid cards" markdown>
- [Click Here to Continue :octicons-arrow-right-24:](installation-explained.md)
</div>