-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Trigger function to auto-update updated_at
CREATE OR REPLACE FUNCTION set_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Owners Table
CREATE TABLE owners (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) NOT NULL UNIQUE,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    phone_number VARCHAR(20),
    address TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    email_verified BOOLEAN NOT NULL DEFAULT FALSE,
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Trigger for owners table
CREATE TRIGGER trigger_set_updated_at_owners
BEFORE UPDATE ON owners
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

-- Pets Table
CREATE TABLE pets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    owner_id UUID NOT NULL,
    name VARCHAR(100) NOT NULL,
    species VARCHAR(50) NOT NULL,
    breed VARCHAR(100),
    date_of_birth DATE,
    gender VARCHAR(10),
    weight DECIMAL(5,2),
    microchip_id VARCHAR(100) UNIQUE,
    medical_notes TEXT,
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE,

    FOREIGN KEY (owner_id) REFERENCES owners(id) ON DELETE CASCADE
);

-- Trigger for pets table
CREATE TRIGGER trigger_set_updated_at_pets
BEFORE UPDATE ON pets
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

-- Insert sample data into owners
INSERT INTO owners (id, email, username, password_hash, full_name, phone_number, address, email_verified)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'alice@example.com', 'alice123', 'hashedpassword1', 'Alice Johnson', '123-456-7890', '123 Apple St', TRUE),
    ('22222222-2222-2222-2222-222222222222', 'bob@example.com', 'bobby88', 'hashedpassword2', 'Bob Smith', '987-654-3210', '456 Orange Ave', FALSE),
    ('33333333-3333-3333-3333-333333333333', 'carol@example.com', 'carol_c', 'hashedpassword3', 'Carol Danvers', '555-555-5555', '789 Banana Blvd', TRUE);

-- Insert sample data into pets
INSERT INTO pets (owner_id, name, species, breed, date_of_birth, gender, weight, microchip_id, medical_notes)
VALUES
    ('11111111-1111-1111-1111-111111111111', 'Buddy', 'Dog', 'Golden Retriever', '2018-06-01', 'Male', 30.5, 'MC-1001', 'Allergic to peanuts.'),
    ('22222222-2222-2222-2222-222222222222', 'Whiskers', 'Cat', 'Siamese', '2020-02-15', 'Female', 4.2, 'MC-1002', 'None'),
    ('33333333-3333-3333-3333-333333333333', 'Hopper', 'Rabbit', 'Lop', '2021-11-20', 'Male', 2.1, 'MC-1003', 'Needs monthly nail trimming.');