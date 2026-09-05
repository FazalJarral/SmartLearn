# Security Threat Model

## Malicious PDFs

The API must validate extension, MIME type, magic bytes, size, parseability, encryption, and page count before AI processing or quota consumption. Parsing must run with bounded memory and time.

## Prompt Injection

Uploaded text is untrusted source material. Prompts must delimit document text and instruct the model not to follow instructions from the document. AI output is validated as strict JSON and escaped in the UI.

## Broken Object Authorization

Every object lookup must authorize against the authenticated user or controlled guest session. Request bodies cannot specify ownership. Signed URLs are issued only after authorization.

## Job Duplication

Upload idempotency keys, unique package rows, worker leases, heartbeats, and retry limits prevent duplicate records and leaked storage objects.

## Signed URL Leakage

Signed URLs must be short-lived, never logged, and only generated server-side for private bucket objects.

## Resource Exhaustion

Hard upload limits, page limits, endpoint rate limits, UTC daily quotas, worker leases, render timeouts, and bounded retries protect the API and worker.
