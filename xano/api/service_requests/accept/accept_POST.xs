// Assigns a pending service request to the authenticated provider
query "{id}/accept" verb=POST {
  api_group = "Service Requests"
  auth = "user"

  input {
    int id
  }

  stack {
    db.get user {
      field_name = "id"
      field_value = $auth.id
    } as $authenticated_user

    db.get service_request {
      field_name = "id"
      field_value = $input.id
    } as $service_request

    precondition ($service_request != null) {
      error_type = "notfound"
      error = "Service request not found."
    }

    precondition ($authenticated_user.role == "prestador") {
      error_type = "accessdenied"
      error = "Only a provider can accept a service request."
    }

    precondition ($service_request.status == "pending" && $service_request.provider_id == null) {
      error_type = "accessdenied"
      error = "This service request is no longer available."
    }

    db.add service_request_acceptance {
      data = {
        service_request_id: $input.id
        provider_id: $auth.id
      }
    } as $acceptance

    db.edit service_request {
      field_name = "id"
      field_value = $input.id
      data = {
        status: "accepted"
        provider_id: $auth.id
      }
    } as $accepted_request
  }

  response = $accepted_request
  tags = ["sosdrive:service_requests"]
}
