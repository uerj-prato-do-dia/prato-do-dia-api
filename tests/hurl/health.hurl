# Fast contract check for the versioned health endpoint.
GET {{base_url}}/v1/health
HTTP 200
[Captures]
duration_ms: duration
[Asserts]
header "Content-Type" contains "application/json"
duration < 5000
jsonpath "$.status" == "ok"
jsonpath "$.service" == "prato-do-dia-api"
