Check whether the database schema exists

Enter Postgres:

docker compose exec postgres psql -U postgres -d cra_compliance

and then 

\dt

we should see all expected tables. If not, our database is not fully migrated yet.

docker compose exec backend alembic upgrade head



%%% Login and get tokens
curl -X POST \
  'http://localhost:8000/api/v1/auth/login' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "email": "admin@example.com",
    "password": "Admin12345!"
  }'



Verify /auth/me
curl -X GET \
  'http://localhost:8000/api/v1/auth/me' \
  -H 'accept: application/json' \
  -H 'Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlMTExZWM2Mi0xOWQ5LTQyNWItYjMzMy1iYjhjMGUzODgzNTIiLCJ0eXBlIjoiYWNjZXNzIiwianRpIjoiMGY2ODA4NDAtN2FiOS00MWU5LTgxZDMtNjZiNjI1Y2NjMjVhIiwiaWF0IjoxNzc0MzU1ODQ2LCJuYmYiOjE3NzQzNTU4NDYsImV4cCI6MTc3NDM1OTQ0Niwicm9sZXMiOlsiYWRtaW4iXSwiZW1haWwiOiJhZG1pbkBleGFtcGxlLmNvbSJ9.E82tavbFSjKuvT54V2YsT9XHKrU1tNhTb9BmISS-fwI'


Store Token in Shell
TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJlMTExZWM2Mi0xOWQ5LTQyNWItYjMzMy1iYjhjMGUzODgzNTIiLCJ0eXBlIjoiYWNjZXNzIiwianRpIjoiMGY2ODA4NDAtN2FiOS00MWU5LTgxZDMtNjZiNjI1Y2NjMjVhIiwiaWF0IjoxNzc0MzU1ODQ2LCJuYmYiOjE3NzQzNTU4NDYsImV4cCI6MTc3NDM1OTQ0Niwicm9sZXMiOlsiYWRtaW4iXSwiZW1haWwiOiJhZG1pbkBleGFtcGxlLmNvbSJ9.E82tavbFSjKuvT54V2YsT9XHKrU1tNhTb9BmISS-fwI'



  Create first product
 curl -i -X POST 'http://localhost:8000/api/v1/products/' \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_code": "PROD-001",
    "name": "Connected Gateway",
    "description": "Industrial edge gateway",
    "parent_product_id": null,
    "manufacturer_name": "Acme Systems",
    "intended_use": "Collects telemetry and forwards data to remote systems",
    "product_type": "hardware_software_system",
    "current_classification": "normal",
    "scope_status": "undecided"
  }'

  See the products
  curl -i -L -X GET 'http://localhost:8000/api/v1/products' \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN"


  1. Get product detail
curl -i -L -X GET 'http://localhost:8000/api/v1/products/fadc8334-d665-4368-8209-51fc835af864' \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN"

2. Run scope evaluation
  curl -i -L -X POST 'http://localhost:8000/api/v1/products/fadc8334-d665-4368-8209-51fc835af864/scope-evaluation' \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "is_digital_product": true,
    "has_network_connectivity": true,
    "performs_remote_data_processing": true,
    "safety_component": false,
    "used_in_critical_sector": true,
    "handles_sensitive_functions": true,
    "excluded_category": false,
    "notes": "Core operational platform for critical infrastructure"
  }'

  Expected result from the current rule engine:

in_scope: true
recommended_classification: "critical"
suggested_conformity_route: "third_party_assessment"


3. Create a release
  curl -i -L -X POST 'http://localhost:8000/api/v1/product-releases' \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "fadc8334-d665-4368-8209-51fc835af864",
    "version": "1.0.0",
    "release_status": "draft",
    "planned_release_date": "2026-04-15T00:00:00Z",
    "actual_release_date": null,
    "classification_snapshot": "critical",
    "conformity_route_snapshot": "third_party_assessment",
    "release_notes": "Initial production candidate"
  }'

  4. Create a remote processing element
  curl -i -L -X POST 'http://localhost:8000/api/v1/remote-processing-elements' \
  -H "accept: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "fadc8334-d665-4368-8209-51fc835af864",
    "name": "Telemetry Analytics Backend",
    "description": "Cloud service used for processing uploaded telemetry",
    "provider_name": "Acme Cloud",
    "data_processed": "Device telemetry and configuration metadata",
    "geographic_location": "eu-central-1",
    "criticality": "high"
  }'


  6. Check audit rows in Postgres

  first 
  docker compose exec postgres psql -U postgres -d cra_compliance
then

SELECT occurred_at, action_type, entity_type, status, details_json
FROM audit_log_events
ORDER BY occurred_at DESC
LIMIT 20;



Run the Alembic migration inside the backend container:

docker compose exec backend alembic upgrade head