Telemetry is flowing into Dynatrace. Logs and spans are being enriched with metadata from both the Kubernetes API and custom pod annotations that we've added to the `cartservice`.

As the developer, you already know that if an error log occurs that contains the content:

```
Wasn't able to connect to Redis.
```

This is serious enough that you immediately want an alert. So you've added the following rule to the collector:

```
processors:
  transform:
    log_statements:
      - context: log
        statements:
          - set(attributes["alertme"], "true")
            where resource.attributes["service.name"] == "cartservice"
            and IsMatch(body, "(?i)wasn't able to connect to redis.*")
```

This uses the [transform processor](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/transformprocessor){target=_blank} to act on each log line,
as it flows through the collector.

Read the rule as follows:

* If the log originates from the `cartservice`
* and the log line contains the phrase `wasn't able to connect to redis` (case insensitive)
* add a new attribute called `alertme` and set the value to `"true"`

In other words, the following log line would **not** be modified:

**input**
```
{
    "status": "INFO",
    "content": "some log line text here"
}
```
