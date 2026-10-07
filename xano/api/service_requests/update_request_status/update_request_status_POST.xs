// Updates the status of an existing service request
query "update_request_status" verb=POST {
  api_group = "Service Requests"
  auth = "user"

  input {
    int request_id
    text status
  }

  stack {
    db.get service_request {
      field_name = "id"
      field_value = $input.request_id
    } as $existing_request

    precondition ($existing_request != null) {
      error_type = "notfound"
      error = "Service request not found."
    }

    db.edit service_request {
      field_name = "id"
      field_value = $input.request_id
      data = {
        status: $input.status
      }
    } as $updated_request
  }

  response = $updated_request
  tags = ["sosdrive:service_requests"]
}
