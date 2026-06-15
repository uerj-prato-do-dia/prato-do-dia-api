# Fetches an overlay URL captured from a successful analyze response.
GET {{base_url}}{{overlay_url}}
HTTP 200
[Captures]
duration_ms: duration
[Asserts]
duration < 10000
header "Content-Type" contains "image"
