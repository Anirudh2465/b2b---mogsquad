-- Database Schema Extensions for Phase 2
-- OCR, Medications, and Adherence Tracking

-- Prescriptions Table
CREATE TABLE IF NOT EXISTS prescriptions (
    prescription_id UUID PRIMARY KEY,
    patient_id UUID NOT NULL,
    prescription_image BYTEA NOT NULL,  -- Encrypted prescription image
    extracted_data JSONB,               -- Structured OCR output
    created_at TIMESTAMP DEFAULT NOW(),
    
    -- Foreign key (assuming patient_records exists)
    CONSTRAINT fk_patient FOREIGN KEY (patient_id) 
        REFERENCES patient_records(patient_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_prescription_patient ON prescriptions(patient_id);
CREATE INDEX IF NOT EXISTS idx_prescription_created ON prescriptions(created_at DESC);

-- Medications Table
CREATE TABLE IF NOT EXISTS medications (
    medication_id UUID PRIMARY KEY,
    patient_id UUID NOT NULL,
    prescription_id UUID NOT NULL,
    
    -- Drug information
    drug_name VARCHAR(255) NOT NULL,
    strength VARCHAR(50) NOT NULL,
    
    -- Frequency
    frequency VARCHAR(50) NOT NULL,     -- Raw text (e.g., "BID", "1-0-1")
    frequency_json JSONB NOT NULL,      -- Parsed schedule with times
    
    -- Duration and inventory
    duration_days INT NOT NULL,
    total_pills INT NOT NULL,
    pills_remaining INT NOT NULL,
    last_taken_at TIMESTAMP,
    refill_threshold INT DEFAULT 5,
    
    -- Pharmacy information
    pharmacy_name VARCHAR(255),
    pharmacy_phone VARCHAR(20),
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_medication_patient FOREIGN KEY (patient_id) 
        REFERENCES patient_records(patient_id) ON DELETE CASCADE,
    CONSTRAINT fk_medication_prescription FOREIGN KEY (prescription_id) 
        REFERENCES prescriptions(prescription_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_medication_patient ON medications(patient_id);
CREATE INDEX IF NOT EXISTS idx_medication_prescription ON medications(prescription_id);
CREATE INDEX IF NOT EXISTS idx_medication_pills_remaining ON medications(pills_remaining);
CREATE INDEX IF NOT EXISTS idx_medication_active ON medications(patient_id, pills_remaining) 
    WHERE pills_remaining > 0;

-- Adherence Events Table
CREATE TABLE IF NOT EXISTS adherence_events (
    event_id UUID PRIMARY KEY,
    medication_id UUID NOT NULL,
    event_type VARCHAR(20) NOT NULL,    -- 'TAKEN', 'MISSED', 'WASTAGE', 'REFILL'
    pills_count INT DEFAULT 1,
    scheduled_time TIMESTAMP,
    actual_time TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT fk_adherence_medication FOREIGN KEY (medication_id) 
        REFERENCES medications(medication_id) ON DELETE CASCADE,
    CONSTRAINT chk_event_type CHECK (event_type IN ('TAKEN', 'MISSED', 'WASTAGE', 'REFILL'))
);

CREATE INDEX IF NOT EXISTS idx_adherence_medication ON adherence_events(medication_id);
CREATE INDEX IF NOT EXISTS idx_adherence_created ON adherence_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_adherence_type ON adherence_events(event_type);

-- Trigger to update medications.updated_at
CREATE OR REPLACE FUNCTION update_medication_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_medication_updated_at
BEFORE UPDATE ON medications
FOR EACH ROW
EXECUTE FUNCTION update_medication_updated_at();

-- Comments
COMMENT ON TABLE prescriptions IS 'Uploaded prescription images with OCR results';
COMMENT ON TABLE medications IS 'Active and historical medication records with inventory tracking';
COMMENT ON TABLE adherence_events IS 'Log of medication adherence events (taken, missed, wastage)';

COMMENT ON COLUMN medications.frequency_json IS 'Parsed frequency schedule: {count_per_day: X, times: [...]}';
COMMENT ON COLUMN medications.pills_remaining IS 'Current pill count for inventory management';
COMMENT ON COLUMN adherence_events.event_type IS 'TAKEN: pill consumed, MISSED: forgot dose, WASTAGE: lost pills, REFILL: restocked';
