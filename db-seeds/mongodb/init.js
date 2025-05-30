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

// Helpers
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
    var r = (Math.random() * 16) | 0,
        v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

let _idCounter = 1000;
function getNextIntId() {
  return _idCounter++;
}

// USERS
const userId = generateUUID();
db.users.insertOne({
  _id: userId,
  email: "user@example.com",
  username: "user1",
  password_hash: "hashed_pass",
  full_name: "Test User",
  phone_number: "1234567890",
  is_active: true,
  email_verified: true,
  roles: ["admin"],
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// CUSTOMERS
db.customers.insertOne({
  _id: generateUUID(),
  email: "customer@example.com",
  username: "cust123",
  password_hash: "secure123",
  full_name: "Customer One",
  phone_number: "9876543210",
  is_active: true,
  email_verified: true,
  preferences: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// POSTS
db.posts.insertOne({
  _id: generateUUID(),
  user_id: userId,
  title: "First Post",
  content: "Hello world!",
  tags: ["intro", "welcome"],
  is_published: true,
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// MOVIES
const movieId = generateUUID();
db.movies.insertOne({
  _id: movieId,
  title: "Gravity Redux",
  description: "Sci-fi drama",
  genre: ["Drama", "Sci-Fi"],
  release_year: 2023,
  duration_minutes: 130,
  rating: 7.8,
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// WATCH HISTORY
db.watch_history.insertOne({
  _id: generateUUID(),
  customer_id: generateUUID(),
  movie_id: movieId,
  watched_at: new Date(),
  device: "mobile",
  progress_percent: 75,
  metadata: {},
  created_at: new Date(),
  updated_at: new Date()
});

// STUDENTS
db.students.insertOne({
  _id: generateUUID(),
  email: "student@example.com",
  full_name: "Student One",
  username: "sone",
  password_hash: "pass123",
  phone_number: "8888888888",
  is_active: true,
  email_verified: true,
  student_type: "full_time",
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// COURSES
db.courses.insertOne({
  _id: generateUUID(),
  instructor_id: userId,
  title: "Intro to AI",
  description: "Learn the basics of artificial intelligence.",
  tags: ["ai", "beginner"],
  is_published: true,
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// PATIENTS
db.patients.insertOne({
  _id: generateUUID(),
  email: "patient@example.com",
  full_name: "Jane Doe",
  date_of_birth: new Date("1990-01-01"),
  phone_number: "1112223333",
  address: "123 Main St",
  gender: "female",
  emergency_contact: { name: "John Doe", phone: "4445556666" },
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// DOCTORS
const doctorId = generateUUID();
db.doctors.insertOne({
  _id: doctorId,
  full_name: "Dr. John Smith",
  specialty: "Cardiology",
  email: "drsmith@example.com",
  phone_number: "7778889999",
  office_location: "Clinic 101",
  is_active: true,
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// APPOINTMENTS
db.appointments.insertOne({
  _id: generateUUID(),
  patient_id: generateUUID(),
  doctor_id: doctorId,
  appointment_time: new Date(),
  status: "confirmed",
  notes: "Follow-up visit",
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// OWNERS
const ownerId = generateUUID();
db.owners.insertOne({
  _id: ownerId,
  email: "owner@example.com",
  username: "owner001",
  password_hash: "securepass",
  full_name: "Pet Owner",
  phone_number: "3334445555",
  address: "456 Park Ave",
  is_active: true,
  email_verified: true,
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// PETS
db.pets.insertOne({
  _id: generateUUID(),
  owner_id: ownerId,
  name: "Buddy",
  species: "Dog",
  breed: "Labrador",
  date_of_birth: new Date("2020-06-15"),
  gender: "male",
  weight: 25.5,
  microchip_id: "MC123456",
  medical_notes: "Healthy",
  metadata: {},
  created_at: new Date(),
  updated_at: new Date(),
});

// ORBITS
const orbitId = getNextIntId();
db.orbits.insertOne({
  _id: orbitId,
  name: "LEO",
  altitude_km: 2000,
  inclination_deg: 98
});

// SATELLITES
const satelliteId = getNextIntId();
db.satellites.insertOne({
  _id: satelliteId,
  name: "SatOne",
  launch_date: new Date("2022-05-01"),
  orbit_id: orbitId
});

// GROUND STATIONS
const stationId = getNextIntId();
db.ground_stations.insertOne({
  _id: stationId,
  name: "Ground Alpha",
  latitude: "45.0N",
  longitude: "93.0W"
});

// PASSES
db.passes.insertOne({
  _id: getNextIntId(),
  satellite_id: satelliteId,
  ground_station_id: stationId,
  start_time: new Date(),
  end_time: new Date(Date.now() + 10 * 60 * 1000)
});



