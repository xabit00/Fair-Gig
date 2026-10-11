# FairGig integration API contracts

All JSON uses `snake_case`. Protected routes require `Authorization: Bearer <access_token>`. Access tokens are HS256 JWTs with issuer `fairgig-auth`, audience `fairgig-services`, a `type` of `access`, and a `role` of `worker`, `verifier`, or `advocate`.

Health routes are public and verify the shared PostgreSQL connection. Routes explicitly marked as stubs do not persist business data.

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
| POST | `/shifts` | worker | `{platform, date, hours_worked, gross_earned, deductions, net_received, screenshot_url?}` | `201` persisted shift |
| GET | `/shifts` | worker | Optional `platform`, `start_date`, `end_date` query parameters | `{shifts, count}` for the signed-in worker |
| GET | `/shifts/{shift_id}` | worker | None | Owned shift |
| PATCH/PUT | `/shifts/{shift_id}` | worker | Any editable shift fields | Updated owned shift |
| DELETE | `/shifts/{shift_id}` | worker | None | `204` |
| GET | `/earnings/summary` | worker | None | `{total_hours, total_gross, total_deductions, total_net, total_shifts, effective_hourly_rate}` |
| POST | `/shifts/import-csv` | worker | `{csv_text, platform}` | `202 {stub, worker_id, platform, rows_detected, message}` |
| GET | `/shifts/verification-queue` | verifier | Optional `verification_status` query parameter | `{shifts, count}` |
| PATCH | `/shifts/{shift_id}/verification` | verifier | `{verification_status, note?}` | Updated shift plus `{verified_by, note, note_persisted}` |

`verification_status` accepts `confirmed`, `discrepancy_flagged`, or `unverifiable` on verifier updates. New records use `pending`. Verification status is persisted; notes are returned with `note_persisted: false` because the shared schema has no verifier-note column.

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
| GET | `/grievances` | worker, verifier, advocate | None | `{grievances}`; workers receive only their own records |
| GET | `/grievances/{id}` | worker, verifier, advocate | None | Grievance; workers are owner-restricted |
| POST | `/grievances` | worker | `{platform, category, description}` | `201` persisted grievance identity/status |
| PATCH | `/grievances/{id}` | owner for description; verifier/advocate for status | `{description?, status?}` | Updated grievance |
| PATCH | `/grievances/{id}/workflow` | advocate | `{status, cluster_id?, tags?}` | Persisted grievance with tags and resolved cluster UUID |

Workflow status accepts `submitted`, `reviewing`, `escalated`, `resolved`, or `closed`.

## Analytics service, port 8005

| Method | Path | Auth role | Request | Success response |
|---|---|---|---|---|
| GET | `/health` | Public | None | `{service, status, database}` |
| GET | `/kpis` | advocate | None | `{suppressed, minimum_group_size, worker_count?, total_net_received?, median_monthly_income?, effective_deduction_percent?}` |
| GET | `/platforms` | advocate | None | `{minimum_group_size, groups: [{platform, worker_count, median_monthly_income, effective_deduction_percent}]}` |
| GET | `/city-zones` | advocate | None | `{minimum_group_size, groups: [{city_zone, worker_count, median_monthly_income}]}` |
| GET | `/analytics/overview` | advocate | Optional `from`, `to` | Privacy-suppressed period overview |
| GET | `/analytics/earnings-trends` | advocate | None | K-anonymous monthly totals |
| GET | `/analytics/platforms` | advocate | Optional `from`, `to` | K-anonymous platform averages |
| GET | `/analytics/zones` | advocate | Optional `from`, `to` | K-anonymous city-zone averages |
| GET | `/analytics/grievances` | advocate | Optional `from`, `to` | K-anonymous grievance-category counts |
| GET | `/analytics/vulnerability` | advocate | Optional `months` | K-anonymous group decline signals |

The service calculates all values from `shifts`. SQL `HAVING` clauses omit every group containing fewer than `K_ANONYMITY_MIN_GROUP` distinct workers, with a default of five.

## Certificate service, port 8006

| Method | Path | Auth role | Request | Success response |
|---|---|---|---|---|
| GET | `/health` | Public | None | `{service, status, database}` |
| GET | `/certificates/income/summary?from=YYYY-MM-DD&to=YYYY-MM-DD` | worker | None | Database-calculated income and verification totals |
| GET | `/certificates/income?from=YYYY-MM-DD&to=YYYY-MM-DD` | worker | None | Downloadable `application/pdf` income certificate |
| POST | `/certificates/preview` | Any signed-in role | `{worker_id?, worker_name?, period?, net_income?, verified_shifts?}` | Print-friendly A4 `text/html` |
| GET | `/certificates/{worker_id}/summary` | Any signed-in role | None | `{stub, worker_id, status, message}` |

Workers can only request their own worker ID. Advocate and verifier access is allowed by the Level 1 boundary and should be narrowed to a documented business need in Level 2.

## Error shape

FastAPI routes return `{detail: "message"}` for validation, authentication, and authorization errors. Express routes follow the same shape. Expected status codes are `401` for missing or invalid authentication, `403` for insufficient role, `409` for duplicate email, and `422` for invalid input.
