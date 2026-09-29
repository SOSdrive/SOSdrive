// Creates a service request for a vehicle owned by the authenticated user
query "request_service" verb=POST {
  api_group = "Service Requests"
  auth = "user"

  input {
    text service_type
    int vehicle_id
    decimal latitude
    decimal longitude
  }

  stack {
    // 1. Vehicle must exist and belong to the authenticated user
    db.get vehicle {
      field_name = "id"
      field_value = $input.vehicle_id
    } as $vehicle

    precondition ($vehicle != null && $vehicle.user_id == $auth.id) {
      error_type = "accessdenied"
      error = "Veiculo invalido ou nao pertence ao usuario."
    }

    // 2. Distance to the reference base (placeholder coordinates)
    var $base_lat { value = -23.5505 }
    var $base_lng { value = -46.6333 }

    function.run "SOS/haversine" {
      input = {
        lat1: $input.latitude,
        lng1: $input.longitude,
        lat2: $base_lat,
        lng2: $base_lng
      }
    } as $distance_km

    // 3. Price by service type (placeholder values)
    var $base_price { value = 50.0 }
    var $price_per_km { value = 2.5 }

    conditional {
      if ($input.service_type == "tire") {
        var.update $base_price { value = 40.0 }
        var.update $price_per_km { value = 2.5 }
      }
      elseif ($input.service_type == "battery") {
        var.update $base_price { value = 60.0 }
        var.update $price_per_km { value = 2.5 }
      }
      elseif ($input.service_type == "mechanical") {
        var.update $base_price { value = 80.0 }
        var.update $price_per_km { value = 3.0 }
      }
      elseif ($input.service_type == "fuel") {
        var.update $base_price { value = 35.0 }
        var.update $price_per_km { value = 2.0 }
      }
    }

    var $estimated_price {
      value = $base_price + ($distance_km * $price_per_km)
    }

    // 4. Save the request
    db.add service_request {
      data = {
        user_id: $auth.id
        vehicle_id: $input.vehicle_id
        service_type: $input.service_type
        latitude: $input.latitude
        longitude: $input.longitude
        distance_km: $distance_km
        estimated_price: $estimated_price
        status: "pending"
      }
    } as $new_request
  }

  response = {
    request_id: $new_request.id,
    estimated_price: $estimated_price,
    distance_km: $distance_km,
    status: $new_request.status
  }
  guid = "wVjCnHV1gptn5aHzT9vid-qRAxo"
}