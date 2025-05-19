CREATE TABLE orbits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100), -- e.g., "LEO-Polar", "GEO-East"
    altitude_km INT,
    inclination_deg INT
);

CREATE TABLE satellites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    launch_date DATE,
    orbit_id INT REFERENCES orbits(id)
);

CREATE TABLE ground_stations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

CREATE TABLE passes (
    id SERIAL PRIMARY KEY,
    satellite_id INT REFERENCES satellites(id) ON DELETE CASCADE,
    ground_station_id INT REFERENCES ground_stations(id) ON DELETE CASCADE,
    start_time TIMESTAMP,
    end_time TIMESTAMP
);