-- Create Orbits Table
CREATE TABLE orbits (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    altitude_km INT,
    inclination_deg INT
);

-- Create Satellites Table
CREATE TABLE satellites (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE,
    launch_date DATE,
    orbit_id INT REFERENCES orbits(id)
);

-- Create Ground Stations Table
CREATE TABLE ground_stations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION
);

-- Create Passes Table
CREATE TABLE passes (
    id SERIAL PRIMARY KEY,
    satellite_id INT REFERENCES satellites(id) ON DELETE CASCADE,
    ground_station_id INT REFERENCES ground_stations(id) ON DELETE CASCADE,
    start_time TIMESTAMP,
    end_time TIMESTAMP
);

-- Insert example orbits
INSERT INTO orbits (name, altitude_km, inclination_deg)
VALUES 
('LEO', 500, 98),
('MEO', 20000, 56),
('GEO', 35786, 0);

-- Insert example satellites
INSERT INTO satellites (name, launch_date, orbit_id)
VALUES 
('Sat-One', '2022-01-15', (SELECT id FROM orbits WHERE name = 'LEO')),
('Sat-Two', '2023-06-01', (SELECT id FROM orbits WHERE name = 'MEO')),
('GeoSat', '2021-11-05', (SELECT id FROM orbits WHERE name = 'GEO'));

-- Insert example ground stations
INSERT INTO ground_stations (name, latitude, longitude)
VALUES 
('Station Alpha', 34.0522, -118.2437),  -- Los Angeles
('Station Beta', 51.5074, -0.1278),     -- London
('Station Gamma', -33.8688, 151.2093);  -- Sydney

-- Insert example passes
INSERT INTO passes (satellite_id, ground_station_id, start_time, end_time)
VALUES 
(
    (SELECT id FROM satellites WHERE name = 'Sat-One'),
    (SELECT id FROM ground_stations WHERE name = 'Station Alpha'),
    '2025-05-22 10:00:00+00',
    '2025-05-22 10:10:00+00'
),
(
    (SELECT id FROM satellites WHERE name = 'Sat-Two'),
    (SELECT id FROM ground_stations WHERE name = 'Station Beta'),
    '2025-05-22 14:30:00+00',
    '2025-05-22 14:45:00+00'
),
(
    (SELECT id FROM satellites WHERE name = 'GeoSat'),
    (SELECT id FROM ground_stations WHERE name = 'Station Gamma'),
    '2025-05-22 18:00:00+00',
    '2025-05-22 18:20:00+00'
);