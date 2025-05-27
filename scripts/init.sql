-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create schemas
CREATE SCHEMA IF NOT EXISTS r2r;
CREATE SCHEMA IF NOT EXISTS mem0;
CREATE SCHEMA IF NOT EXISTS shared;

-- Grant permissions
GRANT ALL ON SCHEMA r2r TO synapse;
GRANT ALL ON SCHEMA mem0 TO synapse;
GRANT ALL ON SCHEMA shared TO synapse;

-- Shared entities table (knowledge graph)
CREATE TABLE IF NOT EXISTS shared.entities (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    source_system TEXT CHECK (source_system IN ('r2r', 'mem0', 'both'))
);

-- Shared relationships table
CREATE TABLE IF NOT EXISTS shared.relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_entity_id UUID REFERENCES shared.entities(id) ON DELETE CASCADE,
    to_entity_id UUID REFERENCES shared.entities(id) ON DELETE CASCADE,
    relationship_type TEXT NOT NULL,
    properties JSONB DEFAULT '{}',
    weight FLOAT DEFAULT 1.0,
    created_at TIMESTAMP DEFAULT NOW(),
    source_system TEXT CHECK (source_system IN ('r2r', 'mem0', 'both'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_entities_embedding ON shared.entities 
    USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_entities_name ON shared.entities(name);
CREATE INDEX IF NOT EXISTS idx_entities_type ON shared.entities(type);
CREATE INDEX IF NOT EXISTS idx_relationships_from_to ON shared.relationships(from_entity_id, to_entity_id);