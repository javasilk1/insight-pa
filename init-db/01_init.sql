-- Creazione utente e database
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'insightpa_user') THEN
        CREATE ROLE insightpa_user WITH LOGIN PASSWORD 'insightpa_pass' CREATEDB;
    END IF;
END$$;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO insightpa_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO insightpa_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO insightpa_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO insightpa_user;

-- Estensioni richieste
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enum per le aree geografiche
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'area_type') THEN
        CREATE TYPE area_type AS ENUM ('centro', 'flumini', 'poetto', 'geremeas', 'mare_pintau');
    END IF;
END$$;

-- Tabella buildings
CREATE TABLE IF NOT EXISTS buildings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    address TEXT NOT NULL,
    coordinates GEOGRAPHY(POINT, 4326) NOT NULL,
    cadastral_data JSONB,
    area_name area_type NOT NULL,
    risk_score NUMERIC(5,2) NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella documents
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    file_name TEXT NOT NULL,
    file_url TEXT NOT NULL,
    document_type TEXT,
    extracted_text TEXT,
    upload_date TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella violations
CREATE TABLE IF NOT EXISTS violations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    violation_type TEXT NOT NULL,
    unauthorized_area_m2 NUMERIC(10,2),
    detected_date DATE,
    status TEXT,
    severity TEXT,
    description TEXT,
    regulatory_norm TEXT
);

-- Tabella document_embeddings
CREATE TABLE IF NOT EXISTS document_embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    qdrant_point_id UUID NOT NULL,
    indexed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tabella risk_history per tracciare cambiamenti nel rischio
CREATE TABLE IF NOT EXISTS risk_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    building_id UUID REFERENCES buildings(id) ON DELETE CASCADE,
    old_risk_score NUMERIC(5,2),
    new_risk_score NUMERIC(5,2) NOT NULL,
    triggered_rules TEXT[],
    reason TEXT,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indici
CREATE INDEX IF NOT EXISTS idx_buildings_coordinates ON buildings USING GIST (coordinates);
CREATE INDEX IF NOT EXISTS idx_buildings_cadastral_data ON buildings USING GIN (cadastral_data);
CREATE INDEX IF NOT EXISTS idx_buildings_risk_score ON buildings (risk_score);
CREATE INDEX IF NOT EXISTS idx_buildings_area ON buildings (area_name);
CREATE INDEX IF NOT EXISTS idx_risk_history_building_id ON risk_history (building_id);
CREATE INDEX IF NOT EXISTS idx_risk_history_recorded_at ON risk_history (recorded_at);

-- Funzione per edifici entro una distanza (vincolo costiero)
CREATE OR REPLACE FUNCTION get_buildings_within_distance(lat DOUBLE PRECISION, lon DOUBLE PRECISION, meters DOUBLE PRECISION)
RETURNS TABLE(
    id UUID,
    address TEXT,
    coordinates GEOGRAPHY(POINT, 4326),
    risk_score NUMERIC(5,2),
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT id, address, coordinates, risk_score, status
    FROM buildings
    WHERE ST_DWithin(
        coordinates,
        ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography,
        meters
    );
END;
$$ LANGUAGE plpgsql;

-- Inserimento dati demo
INSERT INTO buildings (id, address, coordinates, cadastral_data, area_name, risk_score, status)
VALUES
    (
        '11111111-1111-1111-1111-111111111111',
        'Via Cagliari 25',
        ST_GeogFromText('SRID=4326;POINT(9.1837 39.2414)'),
        '{"superficie_catastale": 120, "superficie_autorizzata": 120, "distanza_mare": 650, "has_permesso": true, "has_piscina": false, "has_permesso_piscina": true, "satellite_change_pct": 4, "documenti_contrastanti": false}'::jsonb,
        'centro',
        5.00,
        'compliant'
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        'Via Nord 78',
        ST_GeogFromText('SRID=4326;POINT(9.1600 39.2200)'),
        '{"superficie_catastale": 145, "superficie_autorizzata": 130, "distanza_mare": 520, "has_permesso": true, "has_piscina": true, "has_permesso_piscina": true, "satellite_change_pct": 18, "documenti_contrastanti": false}'::jsonb,
        'flumini',
        45.00,
        'under_review'
    ),
    (
        '33333333-3333-3333-3333-333333333333',
        'Via Sud 150',
        ST_GeogFromText('SRID=4326;POINT(9.1680 39.1980)'),
        '{"superficie_catastale": 210, "superficie_autorizzata": 150, "distanza_mare": 180, "has_permesso": false, "has_piscina": true, "has_permesso_piscina": false, "satellite_change_pct": 35, "documenti_contrastanti": true}'::jsonb,
        'poetto',
        95.00,
        'violation'
    )
ON CONFLICT (id) DO NOTHING;
