The application is running correctly. It is time to introduce a change into the system.

This simulates releasing new functionality to your users in production.

## Inform Dynatrace

First, inform Dynatrace that a change is about to occur.
Namely, you are going to change the `cartServiceFailure` feature flag from `off` to `on`.

Tell Dynatrace about the upcoming change by sending an event (note: This event does **not** actually make the change; you need to do this).

A wrapper script to help you with this.

Run the following:

```
./runtimeChange.sh cartservice cartServiceFailure on
```

Refresh the `cartservice` page and near the bottom you should see the configuration change event.

![configuration changed event](images/configuration-change-event.png)

## Make Change

Open this file: `flags.yaml`

Change the `defaultValue` of `cartServiceFailure` from `"off"` to `"on"` (line Scroll to line `75`)

![feature flag YAML](images/change-feature-flag.png)

Now apply the change by running this command:

```
kubectl apply -f $CODESPACE_VSCODE_FOLDER/flags.yaml
```

<div class="grid cards" markdown>
- [Click Here to Begin :octicons-arrow-right-24:](review-problem.md)
</div>
