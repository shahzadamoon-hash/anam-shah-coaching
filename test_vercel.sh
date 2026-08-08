#!/bin/bash

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

BASE_URL="https://anam-shah-coaching.vercel.app/api"

echo "========================================="
echo "🧪 Testing Vercel API Endpoints"
echo "========================================="

# 1. Login (get token)
echo -e "\n1. Login:"
TOKEN=$(curl -s -X POST $BASE_URL/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"salmankhan@gmail.com","password":"Salman@009"}' \
  | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -n "$TOKEN" ]; then
  echo -e "   ${GREEN}✅ Token: ${TOKEN:0:20}...${NC}"
else
  echo -e "   ${RED}❌ Login failed${NC}"
  exit 1
fi

# Test endpoints
echo -e "\n2. Health Check:"
RESPONSE=$(curl -s $BASE_URL/health)
echo $RESPONSE | grep -q "healthy" && echo -e "   ${GREEN}✅ PASS${NC}" || echo -e "   ${RED}❌ FAIL${NC}"

echo -e "\n3. Profile:"
RESPONSE=$(curl -s -X GET $BASE_URL/users/profile \
  -H "Authorization: Bearer $TOKEN")
echo $RESPONSE | grep -q "user_id" && echo -e "   ${GREEN}✅ PASS${NC}" || echo -e "   ${RED}❌ FAIL${NC}"

echo -e "\n4. Stats:"
RESPONSE=$(curl -s -X GET $BASE_URL/users/stats \
  -H "Authorization: Bearer $TOKEN")
echo $RESPONSE | grep -q "streak_days" && echo -e "   ${GREEN}✅ PASS${NC}" || echo -e "   ${RED}❌ FAIL${NC}"

echo -e "\n5. Enrollments:"
RESPONSE=$(curl -s -X GET $BASE_URL/enrollments/ \
  -H "Authorization: Bearer $TOKEN")
echo $RESPONSE | grep -q "enrollments" && echo -e "   ${GREEN}✅ PASS${NC}" || echo -e "   ${RED}❌ FAIL${NC}"

echo -e "\n6. Courses:"
RESPONSE=$(curl -s -X GET $BASE_URL/courses \
  -H "Authorization: Bearer $TOKEN")
echo $RESPONSE | grep -q "courses" && echo -e "   ${GREEN}✅ PASS${NC}" || echo -e "   ${RED}❌ FAIL${NC}"

echo -e "\n7. Upcoming Assignments:"
RESPONSE=$(curl -s -X GET $BASE_URL/assignments/upcoming \
  -H "Authorization: Bearer $TOKEN")
echo $RESPONSE | grep -q "assignments" && echo -e "   ${GREEN}✅ PASS${NC}" || echo -e "   ${RED}❌ FAIL${NC}"

echo -e "\n8. Leaderboard:"
RESPONSE=$(curl -s -X GET $BASE_URL/community/leaderboard \
  -H "Authorization: Bearer $TOKEN")
echo $RESPONSE | grep -q "leaders" && echo -e "   ${GREEN}✅ PASS${NC}" || echo -e "   ${RED}❌ FAIL${NC}"

echo -e "\n9. Notifications:"
RESPONSE=$(curl -s -X GET $BASE_URL/notifications/unread \
  -H "Authorization: Bearer $TOKEN")
if [ $? -eq 0 ]; then
  echo -e "   ${YELLOW}⚠️ Response: $RESPONSE${NC}"
else
  echo -e "   ${RED}❌ FAIL (404 Not Found)${NC}"
fi

echo ""
echo "========================================="
