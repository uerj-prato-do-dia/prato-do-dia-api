# Explicit real-ML warmup. This may initialize ONNX Runtime sessions.
POST {{base_url}}/v1/ml/warmup
HTTP 200
[Captures]
duration_ms: duration
warmup_status: jsonpath "$.status"
[Asserts]
header "Content-Type" contains "application/json"
duration < 120000
jsonpath "$.status" == "ready"
jsonpath "$.loaded" == true
jsonpath "$.load_duration_ms" exists
jsonpath "$.warnings" exists
