# Project-scoped SSL trust settings for corporate proxy interception (dev only).
# Auto-sourced by venv\Scripts\Activate.ps1 on every activation of this venv.
$certifiPath = & python -c "import certifi; print(certifi.where())"
$env:REQUESTS_CA_BUNDLE = $certifiPath
$env:SSL_CERT_FILE = $certifiPath
$env:CURL_CA_BUNDLE = $certifiPath
