# Using Dynatrace to Detect Problems in Logs

In this hands-on demo, you will send logs from the OpenTelemetry demo application to Dynatrace.
A [Dynatrace OpenPipeline](https://www.dynatrace.com/news/blog/dynatrace-openpipeline-converging-observability-security-and-business-data-at-massive-scale-for-unmatched-analytics-in-context/){target=_blank} will then be created to process these logs during ingestion.
If a error log is found in the `cartservice`, a Dynatrace problem will be created.

## How is the problem created?
You will release a new feature into production. For demo purposes, this new feature intentionally introduces failure into the system.

First you will inform Dynatrace that a change is incoming. This will be done by sending a `CUSTOM_CONFIGURATION` event to Dynatrace.
Then the feature will be enabled by toggling a feature flag.

After a few moments, the error will occur. The `ERROR` logs flowing through the OpenPipeline will trigger the problem.

This demo uses the [OpenTelemetry demo application](https://opentelemetry.io/docs/demo){target=_blank} and the [Dynatrace OpenTelemetry collector distribution](https://docs.dynatrace.com/docs/extend-dynatrace/opentelemetry/collector){target=_blank} ([why might I want to use the Dynatrace OTEL Collector?](resources.md#why-would-i-use-the-dynatrace-otel-collector){target=_blank}).

## Logical Flow

TODO

## Compatibility

| Deployment         | Tutorial Compatible |
|--------------------|---------------------|
| Dynatrace Managed  | ❌                 |
| Dynatrace SaaS     | ✔️                 |

<div class="grid cards" markdown>
- [Click Here to Begin :octicons-arrow-right-24:](getting-started.md)
</div>