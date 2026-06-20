# API

Base URL: `http://localhost:8000`

## `GET /health`

Response:

```json
{ "status": "healthy", "gpu_available": true }
```

## `POST /api/remediate`

Request:

```json
{
  "plugins": [
    { "slug": "contact-form-7", "version": "5.9.2" }
  ]
}
```

Response:

```json
{
  "remediation_plan": "...",
  "vulnerabilities_found": 3
}
```
