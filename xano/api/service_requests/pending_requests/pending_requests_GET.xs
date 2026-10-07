// Lists pending service requests for authenticated providers
query "pending_requests" verb=GET {
  api_group = "Service Requests"
  auth = "user"

  input {
  }

  stack {
    db.query service_request {
      where = $db.service_request.status == "pending"
      join = {
        _user: {
          table: "user"
          type: "left"
          where: $db.service_request.user_id == $db.user.id
        }
        _vehicle: {
          table: "vehicle"
          type: "left"
          where: $db.service_request.vehicle_id == $db.vehicle.id
        }
      }
      return = {type: "list"}
    } as $requests
  }

  response = $requests
  tags = ["sosdrive:service_requests"]
}
