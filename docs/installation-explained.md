The OpenTelemetry demo and the Dynatrace collector will be installed automatically.

The Dynatrace details you provided during startup will be encrypted, stored in GitHub secrets and made available as environment variables (hint: `printenv` to see).

They will also be stored in a Kubernetes secret:

```
kubectl get secret/dynatrace-otelcol-dt-api-credentials -o yaml
```

## Wait for System

Wait for all pods to be Ready (can take up to 10mins)

```
kubectl wait --for condition=Ready pod --timeout=10m --all
```

<div class="grid cards" markdown>
- [Click Here to Continue :octicons-arrow-right-24:](access-ui.md)
</div>