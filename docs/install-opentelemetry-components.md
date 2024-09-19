TODO: Explain what has been installed automatically and what user needs to wait for.

Wait for all pods to be Ready (can take up to 10mins)

```
kubectl wait --for condition=Ready pod --timeout=10m --all
```

## [Click Here to Continue...](access-ui.md)