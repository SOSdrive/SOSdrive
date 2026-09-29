// Calculates distance in km between two points using the Haversine formula
function "SOS/haversine" {
  input {
    decimal lat1
    decimal lng1
    decimal lat2
    decimal lng2
  }

  stack {
    // Convert degrees to radians
    var $r_lat1 { value = $input.lat1|deg2rad }
    var $r_lng1 { value = $input.lng1|deg2rad }
    var $r_lat2 { value = $input.lat2|deg2rad }
    var $r_lng2 { value = $input.lng2|deg2rad }

    var $dlat { value = $r_lat2 - $r_lat1 }
    var $dlng { value = $r_lng2 - $r_lng1 }

    // Pieces of the formula, one step per variable
    var $sin_dlat { value = ($dlat / 2)|sin }
    var $sin_dlng { value = ($dlng / 2)|sin }
    var $cos_lat1 { value = $r_lat1|cos }
    var $cos_lat2 { value = $r_lat2|cos }

    var $a {
      value = ($sin_dlat * $sin_dlat) + ($cos_lat1 * $cos_lat2 * ($sin_dlng * $sin_dlng))
    }
    var $sqrt_a { value = $a|sqrt }
    var $c { value = 2 * ($sqrt_a|asin) }

    // Radius of Earth in km
    var $radius { value = 6371.0 }
    var $result { value = $radius * $c }
  }

  response = $result
  guid = "9369hbWClZmfJqh-nrLHkVUi47k"
}