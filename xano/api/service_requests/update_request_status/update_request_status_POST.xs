// Allows the assigned provider to release a request back to the pending queue
query "update_request_status" verb=POST {
  api_group = "Service Requests"
  auth = "user"

  input {
    int request_id
    text status
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $authenticated_user

    db.get service_request {
      field_name = "id"
      field_value = $input.request_id
    } as $existing_request

    precondition ($existing_request != null) {
      error_type = "notfound"
      error = "Service request not found."
    }

    precondition ($input.status == "pending") {
      error_type = "inputerror"
      error = "Only request cancellation is supported by this endpoint."
    }

    precondition ($existing_request.provider_id == $auth.id && $authenticated_user.role == "prestador") {
      error_type = "accessdenied"
      error = "Only the assigned provider can release this service request."
    }

    db.get service_request_acceptance {
      field_name = "service_request_id"
      field_value = $input.request_id
    } as $acceptance

    conditional {
      if ($acceptance != null) {
        db.del service_request_acceptance {
          field_name = "id"
          field_value = $acceptance.id
        }
      }
    }

    db.edit service_request {
      field_name = "id"
      field_value = $input.request_id
      data = {
        status: $input.status
        provider_id: null
      }
    } as $updated_request
  }

  response = $updated_request
  tags = ["sosdrive:service_requests"]
}
