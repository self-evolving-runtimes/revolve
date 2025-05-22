-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Students Table
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Function to update updated_at
CREATE OR REPLACE FUNCTION set_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for students
CREATE TRIGGER trigger_set_updated_at_students
BEFORE UPDATE ON students
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();


-- Courses Table
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instructor_id UUID not null,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    tags TEXT[] DEFAULT '{}',
    is_published BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Trigger for courses
CREATE TRIGGER trigger_set_updated_at_courses
BEFORE UPDATE ON courses
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

INSERT INTO students (email, full_name, username, password_hash, phone_number, metadata)
VALUES 
('john.doe@example.com', 'John Doe', 'johnnyD', 'hashed_password_1', '+1234567890', '{"enrolled_year": 2022}'),
('jane.smith@example.com', 'Jane Smith', 'janeS', 'hashed_password_2', '+1987654321', '{"major": "Computer Science"}'),
('alex.lee@example.com', 'Alex Lee', 'alexL', 'hashed_password_3', NULL, '{"scholarship": true}');

-- Using subqueries to get example student IDs as instructors
INSERT INTO courses (instructor_id, title, description, tags, is_published, metadata)
VALUES 
((SELECT id FROM students WHERE username = 'johnnyD'), 'Intro to Databases', 'Learn the basics of relational databases.', ARRAY['databases', 'SQL'], TRUE, '{"level": "beginner"}'),
((SELECT id FROM students WHERE username = 'janeS'), 'Web Development 101', 'Introduction to web development using HTML, CSS, and JS.', ARRAY['web', 'frontend'], FALSE, '{"duration": "6 weeks"}'),
((SELECT id FROM students WHERE username = 'alexL'), 'Python for Data Analysis', 'Explore data manipulation and analysis using Python.', ARRAY['python', 'data'], TRUE, '{"tools": ["pandas", "numpy"]}');