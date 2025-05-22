-- Enable UUID generation extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create 'users' table
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    roles TEXT[] NOT NULL DEFAULT '{}',
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Function to update 'updated_at' column
CREATE OR REPLACE FUNCTION set_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for users table
CREATE TRIGGER trigger_set_updated_at
BEFORE UPDATE ON users
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

-- Create 'posts' table
CREATE TABLE posts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Trigger for posts table
CREATE TRIGGER trigger_set_updated_at_posts
BEFORE UPDATE ON posts
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

-- Insert example users
INSERT INTO users (email, username, password_hash, full_name, phone_number, roles, metadata)
VALUES 
('alice@example.com', 'alice123', 'hashed_password_1', 'Alice Johnson', '+1234567890', ARRAY['user'], '{"timezone": "UTC"}'),
('bob@example.com', 'bobbyB', 'hashed_password_2', 'Bob Brown', '+1987654321', ARRAY['admin'], '{"preferred_language": "en"}'),
('carol@example.com', 'carolC', 'hashed_password_3', 'Carol Clark', NULL, ARRAY['user', 'editor'], '{"newsletter": true}');

-- Insert example posts
-- Using subqueries to get user ids
INSERT INTO posts (user_id, title, content, tags, is_published, metadata)
VALUES 
((SELECT id FROM users WHERE username = 'alice123'), 'Alice''s First Post', 'Content of Alice''s post.', ARRAY['intro', 'welcome'], TRUE, '{"views": 10}'),
((SELECT id FROM users WHERE username = 'bobbyB'), 'Bob''s Thoughts', 'Bob writes about Postgres.', ARRAY['tech', 'postgres'], FALSE, '{"likes": 5}'),
((SELECT id FROM users WHERE username = 'carolC'), 'Carol''s Corner', 'Carol shares tips.', ARRAY['tips', 'writing'], TRUE, '{"shares": 2}');