// Lists messages for an existing service request in creation order
query "{id}/messages" verb=GET {
  api_group = "Service Requests"
  auth = "user"

  input {
    int id
  }

  stack {
    db.get service_request {
      field_name = "id"
      field_value = $input.id
    } as $service_request

    precondition ($service_request != null) {
      error_type = "notfound"
      error = "Service request not found."
    }

    precondition ($service_request.user_id == $auth.id || $auth.role == "prestador") {
      error_type = "accessdenied"
      error = "You cannot access messages for this service request."
    }

    db.query service_messages {
      where = $db.service_messages.service_request_id == $input.id
      sort = {created_at: "asc"}
      return = {type: "list"}
    } as $messages
  }

  response = $messages
  tags = ["sosdrive:service_messages"]
}