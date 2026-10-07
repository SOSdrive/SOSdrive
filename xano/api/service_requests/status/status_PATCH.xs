// Completes an accepted or in-progress service request
query "{id}/status" verb=PATCH {
  api_group = "Service Requests"
  auth = "user"

  input {
    int id
    text status
  }

  stack {
    db.get service_request {
      field_name = "id"
      field_value = $input.id
    } as $existing_request

    precondition ($existing_request != null) {
      error_type = "notfound"
      error = "Service request not found."
    }

    precondition ($input.status == "completed") {
      error_type = "inputerror"
      error = "Only completed status is supported by this endpoint."
    }

    precondition ($existing_request.status == "accepted" || $existing_request.status == "in_progress") {
      error_type = "inputerror"
      error = "Service request cannot be completed from its current status."
    }

    db.edit service_request {
      field_name = "id"
      field_value = $input.id
      data = {
        status: "completed"
      }
    } as $updated_request
  }

  response = $updated_request
  tags = ["sosdrive:service_requests"]
}