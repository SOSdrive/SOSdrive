#!/bin/bash

# Xano Integration Smoke Test
# Usage:
# export XANO_BASE_URL="https://your-api-url.xano.io/api:your-id"
# export TOKEN_A="user_a_token"
# export TOKEN_B="user_b_token"
# bash xano_smoke_test.sh

if [ -z "$XANO_BASE_URL" ] || [ -z "$TOKEN_A" ] || [ -z "$TOKEN_B" ]; then
  echo "Error: XANO_BASE_URL, TOKEN_A, and TOKEN_B environment variables must be set."
  exit 1
fi

echo "--- Starting SOS Drive Xano Smoke Tests ---"
echo "Base URL: $XANO_BASE_URL"

# 1. Create Vehicle for User A
echo -e "\n[1/5] Testing POST /vehicles (User A)..."
RESP_VEHICLE=$(curl -s -w "\n%{http_code}" -X POST "$XANO_BASE_URL/vehicles" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"brand": "Toyota", "model": "Corolla", "plate": "TEST123", "year": 2022, "color": "Silver"}')

HTTP_STATUS=$(echo "$RESP_VEHICLE" | tail -n1)
BODY=$(echo "$RESP_VEHICLE" | sed '$d')
echo "Status: $HTTP_STATUS"
echo "Body: $BODY"
if [ "$HTTP_STATUS" != "200" ] && [ "$HTTP_STATUS" != "201" ]; then echo "FAILED: Expected 200/201"; exit 1; fi

VEHICLE_ID=$(echo $BODY | grep -o '"id":[0-9]*' | cut -d: -f2)
echo "Created Vehicle ID: $VEHICLE_ID"

# 2. List Vehicles for User A
echo -e "\n[2/5] Testing GET /my_vehicles (User A)..."
RESP_LIST=$(curl -s -w "\n%{http_code}" -X GET "$XANO_BASE_URL/my_vehicles" \
  -H "Authorization: Bearer $TOKEN_A")

HTTP_STATUS=$(echo "$RESP_LIST" | tail -n1)
BODY=$(echo "$RESP_LIST" | sed '$d')
echo "Status: $HTTP_STATUS"
echo "Body: $BODY"
if [[ "$BODY" != *"$VEHICLE_ID"* ]]; then echo "FAILED: Vehicle not found in list"; exit 1; fi

# 3. Request Service for User A
echo -e "\n[3/5] Testing POST /request_service (User A)..."
RESP_REQ=$(curl -s -w "\n%{http_code}" -X POST "$XANO_BASE_URL/request_service" \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d "{\"service_type\": \"tire\", \"vehicle_id\": $VEHICLE_ID, \"latitude\": -23.55, \"longitude\": -46.63}")

HTTP_STATUS=$(echo "$RESP_REQ" | tail -n1)
BODY=$(echo "$RESP_REQ" | sed '$d')
echo "Status: $HTTP_STATUS"
echo "Body: $BODY"
if [ "$HTTP_STATUS" != "200" ]; then echo "FAILED: Expected 200"; exit 1; fi
if [[ "$BODY" != *"estimated_price"* ]]; then echo "FAILED: Missing estimated_price"; exit 1; fi

# 4. Unauthorized Request (User B requesting User A's vehicle)
echo -e "\n[4/5] Testing POST /request_service (Unauthorized User B)..."
RESP_UNAUTH=$(curl -s -w "\n%{http_code}" -X POST "$XANO_BASE_URL/request_service" \
  -H "Authorization: Bearer $TOKEN_B" \
  -H "Content-Type: application/json" \
  -d "{\"service_type\": \"tire\", \"vehicle_id\": $VEHICLE_ID, \"latitude\": -23.55, \"longitude\": -46.63}")

HTTP_STATUS=$(echo "$RESP_UNAUTH" | tail -n1)
echo "Status: $HTTP_STATUS"
if [ "$HTTP_STATUS" != "403" ]; then echo "FAILED: Expected 403 Forbidden"; exit 1; fi

# 5. Check Request History for User A
echo -e "\n[5/5] Testing GET /my_requests (User A)..."
RESP_HIST=$(curl -s -w "\n%{http_code}" -X GET "$XANO_BASE_URL/my_requests" \
  -H "Authorization: Bearer $TOKEN_A")

HTTP_STATUS=$(echo "$RESP_HIST" | tail -n1)
BODY=$(echo "$RESP_HIST" | sed '$d')
echo "Status: $HTTP_STATUS"
echo "Body: $BODY"
if [[ "$BODY" != *"tire"* ]]; then echo "FAILED: Request not found in history"; exit 1; fi

echo -e "\n--- ALL TESTS PASSED SUCCESSFULLY ---"
