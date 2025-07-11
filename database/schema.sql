-- Google Scholar Profile Analyzer Database Schema
-- PostgreSQL Database

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for authentication
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    institution VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Scholar profiles table
CREATE TABLE scholar_profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    google_scholar_id VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    affiliation VARCHAR(255),
    email_domain VARCHAR(255),
    interests TEXT[],
    h_index INTEGER,
    i10_index INTEGER,
    total_citations INTEGER DEFAULT 0,
    profile_image_url TEXT,
    verified BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Publications table
CREATE TABLE publications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES scholar_profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    authors TEXT NOT NULL,
    venue VARCHAR(500),
    year INTEGER,
    citation_count INTEGER DEFAULT 0,
    pdf_url TEXT,
    google_scholar_url TEXT,
    doi VARCHAR(255),
    abstract TEXT,
    keywords TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Authorship roles table
CREATE TABLE authorship_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES scholar_profiles(id) ON DELETE CASCADE,
    role_type VARCHAR(50) NOT NULL CHECK (role_type IN ('first', 'corresponding', 'student', 'middle', 'last')),
    author_position INTEGER,
    is_primary_author BOOLEAN DEFAULT FALSE,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(publication_id, profile_id)
);

-- Research areas taxonomy
CREATE TABLE research_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) UNIQUE NOT NULL,
    parent_area_id UUID REFERENCES research_areas(id),
    description TEXT,
    level INTEGER DEFAULT 0, -- 0: top level, 1: sub-area, etc.
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Many-to-many relationship between publications and research areas
CREATE TABLE publication_research_areas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    research_area_id UUID REFERENCES research_areas(id) ON DELETE CASCADE,
    confidence_score DECIMAL(3,2) CHECK (confidence_score >= 0 AND confidence_score <= 1),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(publication_id, research_area_id)
);

-- Citation history for time-series analysis
CREATE TABLE citation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publication_id UUID REFERENCES publications(id) ON DELETE CASCADE,
    profile_id UUID REFERENCES scholar_profiles(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    citation_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(publication_id, profile_id, date)
);

-- Profile metrics timeline
CREATE TABLE profile_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES scholar_profiles(id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    total_citations INTEGER DEFAULT 0,
    h_index INTEGER DEFAULT 0,
    i10_index INTEGER DEFAULT 0,
    publication_count INTEGER DEFAULT 0,
    avg_citations_per_paper DECIMAL(10,2) DEFAULT 0,
    collaboration_score DECIMAL(5,2) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(profile_id, metric_date)
);

-- Analysis results cache
CREATE TABLE analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES scholar_profiles(id) ON DELETE CASCADE,
    analysis_type VARCHAR(100) NOT NULL,
    results JSONB NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    version INTEGER DEFAULT 1
);

-- Collaboration networks
CREATE TABLE collaborations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_id UUID REFERENCES scholar_profiles(id) ON DELETE CASCADE,
    collaborator_name VARCHAR(255) NOT NULL,
    collaborator_profile_id UUID REFERENCES scholar_profiles(id),
    collaboration_count INTEGER DEFAULT 1,
    first_collaboration_year INTEGER,
    last_collaboration_year INTEGER,
    shared_publications UUID[],
    collaboration_strength DECIMAL(5,2) DEFAULT 0, -- 0-1 score
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(profile_id, collaborator_name)
);

-- Profile comparison results
CREATE TABLE profile_comparisons (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    profile_ids UUID[] NOT NULL,
    comparison_type VARCHAR(100) NOT NULL,
    results JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Indexes for performance optimization
CREATE INDEX idx_scholar_profiles_google_id ON scholar_profiles(google_scholar_id);
CREATE INDEX idx_scholar_profiles_user_id ON scholar_profiles(user_id);
CREATE INDEX idx_publications_profile_id ON publications(profile_id);
CREATE INDEX idx_publications_year ON publications(year DESC);
CREATE INDEX idx_publications_citation_count ON publications(citation_count DESC);
CREATE INDEX idx_publications_profile_year ON publications(profile_id, year DESC);
CREATE INDEX idx_authorship_roles_profile_id ON authorship_roles(profile_id);
CREATE INDEX idx_authorship_roles_publication_id ON authorship_roles(publication_id);
CREATE INDEX idx_authorship_roles_type ON authorship_roles(role_type);
CREATE INDEX idx_citation_history_profile_date ON citation_history(profile_id, date DESC);
CREATE INDEX idx_citation_history_publication_date ON citation_history(publication_id, date DESC);
CREATE INDEX idx_profile_metrics_profile_date ON profile_metrics(profile_id, metric_date DESC);
CREATE INDEX idx_analysis_results_profile_type ON analysis_results(profile_id, analysis_type);
CREATE INDEX idx_analysis_results_expires ON analysis_results(expires_at);
CREATE INDEX idx_collaborations_profile_id ON collaborations(profile_id);
CREATE INDEX idx_collaborations_strength ON collaborations(collaboration_strength DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_publications_updated_at BEFORE UPDATE ON publications
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_collaborations_updated_at BEFORE UPDATE ON collaborations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample research areas
INSERT INTO research_areas (name, description, level) VALUES
('Computer Science', 'General computer science field', 0),
('Machine Learning', 'Machine learning and artificial intelligence', 1),
('Natural Language Processing', 'Processing and understanding of natural language', 1),
('Computer Vision', 'Computer vision and image processing', 1),
('Data Science', 'Data analysis and data mining', 1),
('Software Engineering', 'Software development and engineering practices', 1),
('Human-Computer Interaction', 'Interaction between humans and computers', 1),
('Cybersecurity', 'Computer and network security', 1),
('Deep Learning', 'Deep neural networks and deep learning', 2),
('Reinforcement Learning', 'Reinforcement learning algorithms', 2),
('Information Retrieval', 'Search and information retrieval systems', 2),
('Speech Recognition', 'Automatic speech recognition', 2),
('Image Classification', 'Classification of images using ML', 2),
('Object Detection', 'Detection and localization of objects in images', 2);

-- Update parent relationships for sub-areas
UPDATE research_areas 
SET parent_area_id = (SELECT id FROM research_areas WHERE name = 'Machine Learning' AND level = 1)
WHERE name IN ('Deep Learning', 'Reinforcement Learning');

UPDATE research_areas 
SET parent_area_id = (SELECT id FROM research_areas WHERE name = 'Natural Language Processing' AND level = 1)
WHERE name IN ('Information Retrieval', 'Speech Recognition');

UPDATE research_areas 
SET parent_area_id = (SELECT id FROM research_areas WHERE name = 'Computer Vision' AND level = 1)
WHERE name IN ('Image Classification', 'Object Detection');