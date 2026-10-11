# FairGig Level 1 API contracts

All JSON uses `snake_case`. Protected routes require `Authorization: Bearer <access_token>`. Access tokens are HS256 JWTs with issuer `fairgig-auth`, audience `fairgig-services`, a `type` of `access`, and a `role` of `worker`, `verifier`, or `advocate`.

Stub routes establish request and response shapes but do not write business data in Level 1. Health routes are public and verify the shared PostgreSQL connection.

## Auth service, port 8001

| Method | Path | Auth role | Request | Success response |
|---|---|---|---|---|
| GET | `/health` | Public | None | `{service, status, database}` |
| POST | `/register` | Public | `{name, email, password, city_zone, category}` | `201 {access_token, refresh_token, token_type, expires_in, user}` |
| POST | `/login` | Public | `{email, password}` | `{access_token, refresh_token, token_type, expires_in, user}` |
| POST | `/refresh` | Public | `{refresh_token}` | Rotated token pair and current `user` |
| GET | `/me` | Any signed-in role | None | `{id, name, email, role, city_zone, category, created_at}` |
| PATCH | `/users/{user_id}/role` | advocate | `{role}` | Updated user object |

Registration always creates a `worker`. An advocate can later assign `worker`, `verifier`, or `advocate`. Refresh tokens are stored as SHA-256 hashes and rotate on every refresh.

## Earnings service, port 8002

| Method | Path | Auth role | Request | Success response |
|---|---|---|---|---|
| GET | `/health` | Public | None | `{service, status, database}` |
| POST | `/shifts` | worker | `{platform, date, hours_worked, gross_earned, deductions, net_received, screenshot_url?}` | `201 {stub, message, shift}` |
| POST | `/shifts/import-csv` | worker | `{csv_text, platform}` | `202 {stub, worker_id, platform, rows_detected, message}` |
| PATCH | `/shifts/{shift_id}/verification` | verifier | `{verification_status, note?}` | `{stub, shift_id, verification_status, note, verified_by}` |

`verification_status` accepts `confirmed`, `discrepancy_flagged`, or `unverifiable` on verifier updates. New records use `pending`.

## Anomaly service, port 8003

| Method | Path | Auth role | Request | Success response |
|---|---|---|---|---|
| GET | `/health` | Public | None | `{service, status, database}` |
| GET | `/rules` | worker, verifier, advocate | None | `{rules: [{id, condition}]}` |
| POST | `/detect` | worker, verifier, advocate | `{worker_id, earnings: [{date, platform, gross_earned, deductions, net_received}]}` | `{worker_id, records_analysed, anomalies, summary}` |

An anomaly is either `{type: "high_deduction", date, platform, value, threshold, explanation}` or `{type: "monthly_income_drop", month, previous_month, value, previous_value, drop_percent, explanation}`.

## Grievance service, port 8004

| Method | Path | Auth role | Request | Success response |
|---|---|---|---|---|
| GET | `/health` | Public | None | `{service, status, database}` |
| GET | `/grievances` | worker, advocate | None | `{stub, viewer, grievances}` |
| POST | `/grievances` | worker | `{platform, category, description}` | `201 {stub, grievance}` |
| PATCH | `/grievances/{id}/workflow` | advocate | `{status, cluster_id?, tags?}` | `{stub, grievance_id, status, cluster_id, tags, updated_by}` |

Workflow status accepts `submitted`, `reviewing`, `escalated`, `resolved`, or `closed`.

## Analytics service, port 8005

| Method | Path | Auth role | Request | Success response |
|---|---|---|---|---|
| GET | `/health` | Public | None | `{service, status, database}` |
| GET | `/kpis` | advocate | None | `{suppressed, minimum_group_size, worker_count?, total_net_received?, median_monthly_income?, effective_deduction_percent?}` |
| GET | `/platforms` | advocate | None | `{minimum_group_size, groups: [{platform, worker_count, median_monthly_income, effective_deduction_percent}]}` |
| GET | `/city-zones` | advocate | None | `{minimum_group_size, groups: [{city_zone, worker_count, median_monthly_income}]}` |

The service calculates all values from `shifts`. SQL `HAVING` clauses omit every group containing fewer than `K_ANONYMITY_MIN_GROUP` distinct workers, with a default of five.

## Certificate service, port 8006

| Method | Path | Auth role | Request | Success response |
|---|---|---|---|---|
| GET | `/health` | Public | None | `{service, status, database}` |
| POST | `/certificates/preview` | Any signed-in role | `{worker_id?, worker_name?, period?, net_income?, verified_shifts?}` | Print-friendly A4 `text/html` |
| GET | `/certificates/{worker_id}/summary` | Any signed-in role | None | `{stub, worker_id, status, message}` |

Workers can only request their own worker ID. Advocate and verifier access is allowed by the Level 1 boundary and should be narrowed to a documented business need in Level 2.

## Error shape

FastAPI routes return `{detail: "message"}` for validation, authentication, and authorization errors. Express routes follow the same shape. Expected status codes are `401` for missing or invalid authentication, `403` for insufficient role, `409` for duplicate email, and `422` for invalid input.

