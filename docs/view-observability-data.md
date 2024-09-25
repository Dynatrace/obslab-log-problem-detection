In Dynatrace, press `ctrl + k` and search for `Services`. Dynatrace creates service entities based on the incoming span data.
The logs are also available for each service.

You can also query data via [notebooks](https://docs.dynatrace.com/docs/observe-and-explore/dashboards-and-notebooks/notebooks){target=_blank}
and [dashboards](https://docs.dynatrace.com/docs/observe-and-explore/dashboards-and-notebooks/dashboards-new){target=_blank} (`ctrl + k` and search for `notebooks` or `dashboards`).

For example, to validate logs are available for `cartservice`:

```
fetch logs
| filter service.name == "cartservice"
| limit 10
```

<div class="grid cards" markdown>
- [Click Here to Continue :octicons-arrow-right-24:](introduce-change.md)
</div>