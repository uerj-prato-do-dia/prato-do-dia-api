# Lightweight contract check. This must not initialize ONNX Runtime sessions.
GET {{base_url}}/v1/ml/status
HTTP 200
[Captures]
duration_ms: duration
model_status: jsonpath "$.status"
[Asserts]
header "Content-Type" contains "application/json"
duration < 10000
jsonpath "$.status" exists
jsonpath "$.status" matches /^(available|unavailable)$/
jsonpath "$.available" exists
jsonpath "$.loaded" exists
jsonpath "$.models" exists
jsonpath "$.warnings" exists
