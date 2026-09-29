// Lists the authenticated user's vehicles
query "my_vehicles" verb=GET {
  api_group = "Service Requests"
  auth = "user"

  input {
  }

  stack {
    db.query vehicle {
      where = $db.vehicle.user_id == $auth.id
      return = {type: "list"}
    } as $vehicles
  }

  response = $vehicles
  guid = "_IyZUtoHuA5kqCvrPpCsIuDNLgg"
}