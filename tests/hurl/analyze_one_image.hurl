# Real-ML smoke/contract check for one uploaded meal image.
# The multipart part is intentionally sent as image/jpeg, matching the mobile client.
POST {{base_url}}/v1/meals/analyze
[Multipart]
file: file,{{image_path}}; image/jpeg

HTTP 200
[Captures]
status: jsonpath "$.status"
analysis_id: jsonpath "$.analysis_id"
original_url: jsonpath "$.image.original_url"
overlay_url: jsonpath "$.image.overlay_url"
duration_ms: duration
[Asserts]
header "Content-Type" contains "application/json"
duration < 60000
jsonpath "$.schema_version" == "1.0"
jsonpath "$.status" matches /^(success|empty)$/
jsonpath "$.analysis_id" exists
jsonpath "$.warnings" exists
jsonpath "$.components" exists
jsonpath "$.image.original_url" exists
