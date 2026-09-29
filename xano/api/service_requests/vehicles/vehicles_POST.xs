query "vehicles" verb=POST {
  api_group = "Service Requests"
  auth = "user"

  input {
    text brand
    text model
    text plate
    int year
    text color
  }

  stack {
    db.add vehicle {
      data = {
        user_id: $auth.id
        brand: $input.brand
        model: $input.model
        plate: $input.plate
        year: $input.year
        color: $input.color
      }
    } as $new_vehicle
  }

  response = $new_vehicle
  guid = "h-gdpp117T496gW0gn0B15AQLLw"
}
