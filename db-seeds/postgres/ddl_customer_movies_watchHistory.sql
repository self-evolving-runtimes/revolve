-- Enable UUIDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Customers Table
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    preferences JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Movies Table
CREATE TABLE movies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    genre TEXT[],
    release_year INT,
    duration_minutes INT,
    rating DECIMAL(2,1), -- e.g. 7.5
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Watch History Table
CREATE TABLE watch_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id UUID NOT NULL ,
    movie_id UUID NOT NULL,
    watched_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    device VARCHAR(100), -- e.g. 'iPhone', 'Smart TV', etc.
    progress_percent INT CHECK (progress_percent BETWEEN 0 AND 100),
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- updated_at trigger function
CREATE OR REPLACE FUNCTION set_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER trigger_set_updated_at_customers
BEFORE UPDATE ON customers
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

CREATE TRIGGER trigger_set_updated_at_movies
BEFORE UPDATE ON movies
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

CREATE TRIGGER trigger_set_updated_at_watch_history
BEFORE UPDATE ON watch_history
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

INSERT INTO customers (email, username, password_hash, full_name, phone_number, preferences)
VALUES 
('john.doe@example.com', 'johnnyD', 'hashed_pass_1', 'John Doe', '+15551234567', '{"genre_preferences": ["Action", "Sci-Fi"]}'),
('jane.smith@example.com', 'janeS', 'hashed_pass_2', 'Jane Smith', '+15559876543', '{"notifications": {"email": true}}'),
('alice.w@example.com', 'aliceW', 'hashed_pass_3', 'Alice Wonder', NULL, '{"theme": "dark", "language": "en"}');

INSERT INTO movies (title, description, genre, release_year, duration_minutes, rating, metadata)
VALUES 
('Inception', 'A thief who steals corporate secrets through use of dream-sharing technology.', ARRAY['Sci-Fi', 'Thriller'], 2010, 148, 8.8, '{"director": "Christopher Nolan"}'),
('The Matrix', 'A hacker learns about the true nature of reality and his role in the war against its controllers.', ARRAY['Action', 'Sci-Fi'], 1999, 136, 8.7, '{"box_office": "465M"}'),
('The Godfather', 'The aging patriarch of an organized crime dynasty transfers control to his reluctant son.', ARRAY['Crime', 'Drama'], 1972, 175, 9.2, '{"awards": ["Oscar", "Golden Globe"]}');

INSERT INTO watch_history (customer_id, movie_id, device, progress_percent, metadata)
VALUES 
((SELECT id FROM customers WHERE username = 'johnnyD'), 
 (SELECT id FROM movies WHERE title = 'Inception'), 
 'Smart TV', 
 100, 
 '{"subtitles": "on"}'),

((SELECT id FROM customers WHERE username = 'janeS'), 
 (SELECT id FROM movies WHERE title = 'The Matrix'), 
 'Laptop', 
 80, 
 '{"paused_at": "1:05:00"}'),

((SELECT id FROM customers WHERE username = 'aliceW'), 
 (SELECT id FROM movies WHERE title = 'The Godfather'), 
 'iPhone', 
 45, 
 '{"rewatched": false}');