// Creates an authenticated message for an existing service request
query "{id}/messages" verb=POST {
  api_group = "Service Requests"
  auth = "user"

  input {
    int id
    text message_text filters=trim
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

    precondition ($input.message_text != "") {
      error_type = "inputerror"
      error = "Message text is required."
    }

    db.add service_messages {
      data = {
        service_request_id: $input.id
        sender_id: $auth.id
        message_text: $input.message_text
      }
    } as $new_message
  }

  response = $new_message
  tags = ["sosdrive:service_messages"]
}