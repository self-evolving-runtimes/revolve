db = db.getSiblingDB("mydb");

db.createCollection("posts", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'user_id', 'title', 'content', 'tags', 'is_published', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "user_id": {'bsonType': 'string'},
        "title": {'bsonType': 'string'},
        "content": {'bsonType': 'string'},
        "tags": {'bsonType': 'array', 'items': {'bsonType': 'string'}},
        "is_published": {'bsonType': 'bool'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("customers", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'email', 'username', 'password_hash', 'full_name', 'phone_number', 'is_active', 'email_verified', 'preferences', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "email": {'bsonType': 'string'},
        "username": {'bsonType': 'string'},
        "password_hash": {'bsonType': 'string'},
        "full_name": {'bsonType': 'string'},
        "phone_number": {'bsonType': 'string'},
        "is_active": {'bsonType': 'bool'},
        "email_verified": {'bsonType': 'bool'},
        "preferences": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("movies", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'title', 'description', 'genre', 'release_year', 'duration_minutes', 'rating', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "title": {'bsonType': 'string'},
        "description": {'bsonType': 'string'},
        "genre": {'bsonType': 'array', 'items': {'bsonType': 'string'}},
        "release_year": {'bsonType': 'int'},
        "duration_minutes": {'bsonType': 'int'},
        "rating": {'bsonType': 'double'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("watch_history", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'customer_id', 'movie_id', 'watched_at', 'device', 'progress_percent', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "customer_id": {'bsonType': 'string'},
        "movie_id": {'bsonType': 'string'},
        "watched_at": {'bsonType': 'date'},
        "device": {'bsonType': 'string'},
        "progress_percent": {'bsonType': 'int'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("patients", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'email', 'full_name', 'date_of_birth', 'phone_number', 'address', 'gender', 'emergency_contact', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "email": {'bsonType': 'string'},
        "full_name": {'bsonType': 'string'},
        "date_of_birth": {'bsonType': 'date'},
        "phone_number": {'bsonType': 'string'},
        "address": {'bsonType': 'string'},
        "gender": {'bsonType': 'string'},
        "emergency_contact": {'bsonType': 'object'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("doctors", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'full_name', 'specialty', 'email', 'phone_number', 'office_location', 'is_active', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "full_name": {'bsonType': 'string'},
        "specialty": {'bsonType': 'string'},
        "email": {'bsonType': 'string'},
        "phone_number": {'bsonType': 'string'},
        "office_location": {'bsonType': 'string'},
        "is_active": {'bsonType': 'bool'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("users", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'email', 'username', 'password_hash', 'full_name', 'phone_number', 'is_active', 'email_verified', 'roles', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "email": {'bsonType': 'string'},
        "username": {'bsonType': 'string'},
        "password_hash": {'bsonType': 'string'},
        "full_name": {'bsonType': 'string'},
        "phone_number": {'bsonType': 'string'},
        "is_active": {'bsonType': 'bool'},
        "email_verified": {'bsonType': 'bool'},
        "roles": {'bsonType': 'array', 'items': {'bsonType': 'string'}},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("courses", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'instructor_id', 'title', 'description', 'tags', 'is_published', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "instructor_id": {'bsonType': 'string'},
        "title": {'bsonType': 'string'},
        "description": {'bsonType': 'string'},
        "tags": {'bsonType': 'array', 'items': {'bsonType': 'string'}},
        "is_published": {'bsonType': 'bool'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("students", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ['_id', 'email', 'full_name', 'username', 'password_hash', 'phone_number', 'is_active', 'email_verified', 'student_type', 'created_at', 'updated_at'],
      properties: {
        "_id": { bsonType: "string" },
        "email": { bsonType: "string" },
        "full_name": { bsonType: "string" },
        "username": { bsonType: "string" },
        "password_hash": { bsonType: "string" },
        "phone_number": { bsonType: "string" },
        "is_active": { bsonType: "bool" },
        "email_verified": { bsonType: "bool" },
        "metadata": { bsonType: "object" },
        "student_type": {
          bsonType: "string",
          enum: ["full_time", "part_time", "exchange"],
          description: "must be one of: full_time, part_time, exchange"
        },
        "created_at": { bsonType: "date" },
        "updated_at": { bsonType: "date" },
        "deleted_at": { bsonType: ["date", "null"] }
      }
    }
  }
});

db.createCollection("appointments", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'patient_id', 'doctor_id', 'appointment_time', 'status', 'notes', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "patient_id": {'bsonType': 'string'},
        "doctor_id": {'bsonType': 'string'},
        "appointment_time": {'bsonType': 'date'},
        "status": {'bsonType': 'string'},
        "notes": {'bsonType': 'string'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("owners", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'email', 'username', 'password_hash', 'full_name', 'phone_number', 'address', 'is_active', 'email_verified', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "email": {'bsonType': 'string'},
        "username": {'bsonType': 'string'},
        "password_hash": {'bsonType': 'string'},
        "full_name": {'bsonType': 'string'},
        "phone_number": {'bsonType': 'string'},
        "address": {'bsonType': 'string'},
        "is_active": {'bsonType': 'bool'},
        "email_verified": {'bsonType': 'bool'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("pets", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'owner_id', 'name', 'species', 'breed', 'date_of_birth', 'gender', 'weight', 'microchip_id', 'medical_notes', 'created_at', 'updated_at'],
      properties: {
        "_id": {'bsonType': 'string'},
        "owner_id": {'bsonType': 'string'},
        "name": {'bsonType': 'string'},
        "species": {'bsonType': 'string'},
        "breed": {'bsonType': 'string'},
        "date_of_birth": {'bsonType': 'date'},
        "gender": {'bsonType': 'string'},
        "weight": {'bsonType': 'double'},
        "microchip_id": {'bsonType': 'string'},
        "medical_notes": {'bsonType': 'string'},
        "metadata": {'bsonType': 'object'},
        "created_at": {'bsonType': 'date'},
        "updated_at": {'bsonType': 'date'},
        "deleted_at": {'bsonType': 'date'}
      }
    }
  }
});

db.createCollection("orbits", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'name', 'altitude_km', 'inclination_deg'],
      properties: {
        "_id": {'bsonType': 'int'},
        "name": {'bsonType': 'string'},
        "altitude_km": {'bsonType': 'int'},
        "inclination_deg": {'bsonType': 'int'}
      }
    }
  }
});

db.createCollection("satellites", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'name', 'launch_date', 'orbit_id'],
      properties: {
        "_id": {'bsonType': 'int'},
        "name": {'bsonType': 'string'},
        "launch_date": {'bsonType': 'date'},
        "orbit_id": {'bsonType': 'int'}
      }
    }
  }
});

db.createCollection("ground_stations", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'name', 'latitude', 'longitude'],
      properties: {
        "_id": {'bsonType': 'int'},
        "name": {'bsonType': 'string'},
        "latitude": {'bsonType': 'string'},
        "longitude": {'bsonType': 'string'}
      }
    }
  }
});

db.createCollection("passes", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      "required": ['_id', 'satellite_id', 'ground_station_id', 'start_time', 'end_time'],
      properties: {
        "_id": {'bsonType': 'int'},
        "satellite_id": {'bsonType': 'int'},
        "ground_station_id": {'bsonType': 'int'},
        "start_time": {'bsonType': 'date'},
        "end_time": {'bsonType': 'date'}
      }
    }
  }
});