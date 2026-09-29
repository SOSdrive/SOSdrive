// Lists the authenticated user's service requests
query "my_requests" verb=GET {
  api_group = "Service Requests"
  auth = "user"

  input {
  }

  stack {
    db.query service_request {
      where = $db.service_request.user_id == $auth.id
      return = {type: "list"}
    } as $requests
  }

  response = $requests
  guid = "i52gs6OXjhPr0JTQ90iXWmpyiPE"
}