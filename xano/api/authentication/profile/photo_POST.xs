// Upload a profile photo for the authenticated user.
query "user_profile/photo" verb=POST {
  api_group = "Authentication"
  auth = "user"

  input {
    file? foto_perfil
  }

  stack {
    precondition ($input.foto_perfil != null) {
      error_type = "inputerror"
      error = "A profile photo is required."
    }

    storage.create_image {
      value = $input.foto_perfil
      access = "public"
      filename = $input.foto_perfil.name
    } as $stored_photo
  }

  response = {
    path: $stored_photo.path
  }

  tags = ["sosdrive:profile"]
}
