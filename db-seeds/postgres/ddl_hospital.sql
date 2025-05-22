-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Patients Table
CREATE TABLE patients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE,
    full_name VARCHAR(100) NOT NULL,
    date_of_birth DATE,
    phone_number VARCHAR(20),
    address TEXT,
    gender VARCHAR(10),
    emergency_contact JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Doctors Table
CREATE TABLE doctors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100),
    email VARCHAR(255) UNIQUE,
    phone_number VARCHAR(20),
    office_location TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    metadata JSONB DEFAULT '{}'::JSONB,

    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- Appointments Table
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    patient_id UUID NOT NULL ,
    doctor_id UUID NOT NULL ,
    appointment_time TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'scheduled', -- scheduled, completed, canceled
    notes TEXT,
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

-- Triggers for updated_at
CREATE TRIGGER trigger_set_updated_at_patients
BEFORE UPDATE ON patients
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

CREATE TRIGGER trigger_set_updated_at_doctors
BEFORE UPDATE ON doctors
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

CREATE TRIGGER trigger_set_updated_at_appointments
BEFORE UPDATE ON appointments
FOR EACH ROW
EXECUTE PROCEDURE set_updated_at_column();

INSERT INTO patients (email, full_name, date_of_birth, phone_number, address, gender, emergency_contact, metadata)
VALUES
('maria.fernandez@example.com', 'Maria Fernandez', '1990-05-12', '+1234567890', '123 Maple Street, Springfield', 'Female',
 '{"name": "Luis Fernandez", "relation": "Brother", "phone": "+1234567899"}',
 '{"insurance": "Plan A"}'),

('david.lee@example.com', 'David Lee', '1985-08-30', '+1234567891', '456 Oak Avenue, Metropolis', 'Male',
 '{"name": "Laura Lee", "relation": "Wife", "phone": "+1234567898"}',
 '{"chronic_conditions": ["diabetes"]}'),

('sara.khan@example.com', 'Sara Khan', '1995-02-20', '+1234567892', '789 Pine Road, Gotham', 'Female',
 '{"name": "Ayesha Khan", "relation": "Mother", "phone": "+1234567897"}',
 '{"allergies": ["penicillin"]}');

 INSERT INTO doctors (full_name, specialty, email, phone_number, office_location, metadata)
VALUES
('Dr. John Smith', 'Cardiology', 'dr.johnsmith@example.com', '+1987654321', 'Room 101, Heart Care Center',
 '{"availability": ["Mon", "Wed", "Fri"]}'),

('Dr. Emily Zhang', 'Dermatology', 'dr.emilyzhang@example.com', '+1987654322', 'Room 203, Skin Clinic',
 '{"languages": ["English", "Mandarin"]}'),

('Dr. Ahmed Al-Farouq', 'Pediatrics', 'dr.ahmed@example.com', '+1987654323', 'Room 305, Children’s Hospital',
 '{"experience_years": 12}');

 INSERT INTO appointments (patient_id, doctor_id, appointment_time, status, notes, metadata)
VALUES
(
 (SELECT id FROM patients WHERE email = 'maria.fernandez@example.com'),
 (SELECT id FROM doctors WHERE full_name = 'Dr. John Smith'),
 '2025-06-01 10:30:00+00',
 'scheduled',
 'Follow-up on blood pressure medication',
 '{"priority": "high"}'
),

(
 (SELECT id FROM patients WHERE email = 'david.lee@example.com'),
 (SELECT id FROM doctors WHERE full_name = 'Dr. Emily Zhang'),
 '2025-06-02 14:00:00+00',
 'completed',
 'Routine skin check completed',
 '{"duration_minutes": 30}'
),

(
 (SELECT id FROM patients WHERE email = 'sara.khan@example.com'),
 (SELECT id FROM doctors WHERE full_name = 'Dr. Ahmed Al-Farouq'),
 '2025-06-03 09:00:00+00',
 'canceled',
 'Appointment canceled by patient due to illness',
 '{"canceled_by": "patient"}'
);