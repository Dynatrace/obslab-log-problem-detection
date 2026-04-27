## Hurry up and wait

--8<-- "snippets/bizevent-installation-explained.js"

!!! warning "Grab a Coffee"
    Everything is installing. This can take a while.

    While you wait, the section below will explain what you've just configured and how it works.

The OpenTelemetry demo and the Dynatrace collector will be installed automatically.

The Dynatrace details you provided during startup will be encrypted, stored in GitHub secrets and made available as environment variables.

They will also be stored in a Kubernetes secret `dynatrace-otelcol-dt-api-credentials`

!!! tip
    Type `printenv` to see all environment variables
    set by GitHub.

## Explain the Configuration

!!! tip "OpenTelemetry Experts Need Not Apply"
    If you already understand OpenTelemetry, the collector, OTTL
    and are comfortable reading the collector configuration file,
    you can probably skip this section.

The pipeline setup in the previous section contained references to lots of fields such as `priority`, `alertmessage` and `dt.owner`.

How did all of those fields get there? Remember, this demo does not modify any of the application code.

### 1. Pod Annotations

First, the developer adds additional, custom annotations to the microservice they are interested in. In this case, the `cartservice`.

They do this by adding some Key/Value pairs to the `podAnnotations` (see [otel-demo-values.yaml](https://github.com/Dynatrace/obslab-log-problem-detection/blob/6314352aaeefc489d8d0096b787a981c81831f59/otel-demo-values.yaml#L20){target=_blank}).

During initialisation, the codespace replaces the placeholder text with your tenant details and notebook ID (see [post-create.sh](https://github.com/Dynatrace/obslab-log-problem-detection/blob/6314352aaeefc489d8d0096b787a981c81831f59/.devcontainer/post-create.sh#L38){target=_blank}).

It is important to realise that the developer is in full control of these K/V pairs.
They can add as many or few as they wish.

You can see these annotations with this command:

```
kubectl describe pod -l app.kubernetes.io/component=cart
```

![podAnnotations](images/podAnnotations.png)

### 2. Collector Enriches Logs

Logs are [sent out of the cart via OpenTelemetry Protocol (OTLP)](https://opentelemetry.io/docs/demo/services/cart/#logs){target=_blank} to the collector.

As log lines flow [through the collector pipeline](https://github.com/Dynatrace/obslab-log-problem-detection/blob/main/collector-values.yaml#L148){target=_blank},
the logs are processed by two `processors`: The [k8sattributes](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/k8sattributesprocessor){target=_blank} and [transform](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/transformprocessor){target=_blank} processors.

### k8sattributes Processor

The [k8sattributes](https://github.com/open-telemetry/opentelemetry-collector-contrib/blob/main/processor/k8sattributesprocessor){target=_blank} interacts with the Kubernetes API to extract important k8s metadata such as pod names, deployment names, node names and other topology-relevant information.

This processor also [pulls selected annotations from pods](https://github.com/Dynatrace/obslab-log-problem-detection/blob/6314352aaeefc489d8d0096b787a981c81831f59/collector-values.yaml#L49){target=_blank}. Namely, the custom annotations that were set in step one.

!!! info
    Notice also that the `key`s are renamed in realtime to Dynatrace-relevant keys. (eg. `ownedBy` becomes `dt.owner`).

All of this information: the k8s metadata and custom annotations are dynamically added to each log line and span as it flows through the collector.
 
Thus this log line:
 
```
2024-10-01 10:00:00 INFO A log message
```

May become:

```
2024-10-01 10:00:00 INFO A log message dt.owner=Susan k8s.pod-name=cart-abc1234 ...
```

### transform Processor

The [transform](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/processor/transformprocessor){target=_blank} processor modifies the telemetry (eg. log line content and attributes) based on the [OpenTelemetry Transformation Language](https://github.com/open-telemetry/opentelemetry-collector-contrib/tree/main/pkg/ottl){target=_blank}.

The collector creates new dynatrace-relevant attributes based on existing attributes. [For example](https://github.com/Dynatrace/obslab-log-problem-detection/blob/6314352aaeefc489d8d0096b787a981c81831f59/collector-values.yaml#L106){target=_blank}, taking `k8s.deployment.name` and creating a new attribute called `dt.kubernetes.workload.name` with the same value.

Two brand new attributes `alertmessage` and `priority` are dynamically added (see [here](https://github.com/Dynatrace/obslab-log-problem-detection/blob/6314352aaeefc489d8d0096b787a981c81831f59/collector-values.yaml#L123){target=_blank}) based on conditions we specify.

* `alertmessage` is intended as a place for the developer to indicate a human readable alert message.
* `priority` is intended as a place for the developer to indicate the importance of this error.

```
- set(attributes["alertmessage"], "Critical Redis connection error!")
  where resource.attributes["service.name"] == "cart"
  and resource.attributes["deployment.release_stage"] == "production"
  and IsMatch(body, "(?i)wasn't able to connect to redis.*")

- set(attributes["priority"], "1")
  where resource.attributes["service.name"] == "cart"
  and resource.attributes["deployment.release_stage"] == "production"
  and IsMatch(body, "(?i)wasn't able to connect to redis.*")
```

!!! success "OpenPipeline Integration"
    The previous steps demonstrate how the logs are enriched with additional metadata.

    OpenPipeline can then use these fields as logs flow into Dynatrace.

## Wait for System

The system may still be loading.

Wait until the `Running postCreate command` loading spinner disappears.

![codespace loading](images/codespace-loading.png)

Wait here until the terminal prompt looks like this (your username will differ).

![codespace interactive](images/codespace-interactive.png)

## Wait for Application

The Kubernetes cluster is available and the application is starting.

Wait for all pods to be Ready (can take up to 10mins)

```
kubectl wait --for condition=Ready pod --timeout=10m --all
```

The command will appear to hang until all pods are available.

When all pods are running, the output will look like this:

```
pod/accounting-58ff999fb7-m2brb condition met
pod/ad-597686b699-8fgqv condition met
pod/cart-7f67699fd8-b9gk6 condition met
pod/checkout-866774f77f-c97rj condition met
pod/currency-659fb4bdf6-4r62x condition met
pod/dynatrace-collector-opentelemetry-collector-6b68486fb9-7hq48 condition met
pod/email-5dd85846c-xfqsg condition met
pod/flagd-fb5756f54-c68dd condition met
pod/fraud-detection-6fc57f5c5c-8vbx8 condition met
pod/frontend-7ff446b4d6-4fqjf condition met
pod/frontend-proxy-7cdb64d859-fxjhb condition met
pod/image-provider-7d59bccf66-vpqnc condition met
pod/kafka-698c55c764-z9qpj condition met
pod/llm-7d86d8f46c-f4plh condition met
pod/load-generator-584d65648b-sh9jq condition met
pod/payment-d97d79558-mdcvj condition met
pod/postgresql-66fff77f5d-dknct condition met
pod/product-catalog-8678c57d69-lr7gt condition met
pod/product-reviews-6c468d787b-x7pfd condition met
pod/quote-67b4d657bf-wvn57 condition met
pod/recommendation-5ddd958c5c-s47sb condition met
pod/shipping-c4f9b46c8-f8z9f condition met
pod/valkey-cart-779654c7f4-6c8km condition met
```

<div class="grid cards" markdown>
- [Click Here to Continue :octicons-arrow-right-24:](access-ui.md)
</div>