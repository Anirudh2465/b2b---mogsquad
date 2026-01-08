-- Database Schema for AuraHealth Sharded Patient Records
-- Run this on BOTH Shard 0 and Shard 1

-- Create database (run separately for each shard)
-- CREATE DATABASE aurahealth_shard0;
-- CREATE DATABASE aurahealth_shard1;

-- Extension for UUID support
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Patient Records Table
CREATE TABLE IF NOT EXISTS patient_records (
    patient_id UUID PRIMARY KEY,
    encrypted_name BYTEA NOT NULL,         -- AES-256-GCM encrypted patient name
    encrypted_history BYTEA NOT NULL,      -- AES-256-GCM encrypted medical history
    shard_id INT NOT NULL,                 -- Shard identifier for validation
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Index on shard_id for validation queries
CREATE INDEX IF NOT EXISTS idx_patient_shard ON patient_records(shard_id);

-- Index on created_at for time-based queries
CREATE INDEX IF NOT EXISTS idx_patient_created ON patient_records(created_at);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_patient_updated_at 
BEFORE UPDATE ON patient_records
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- Comments for documentation
COMMENT ON TABLE patient_records IS 'Encrypted patient medical records distributed across shards';
COMMENT ON COLUMN patient_records.patient_id IS 'Unique patient identifier (UUID)';
COMMENT ON COLUMN patient_records.encrypted_name IS 'AES-256-GCM encrypted patient name with IV and auth tag';
COMMENT ON COLUMN patient_records.encrypted_history IS 'AES-256-GCM encrypted medical history with IV and auth tag';
COMMENT ON COLUMN patient_records.shard_id IS 'Shard assignment based on hash(patient_id) % 2';
