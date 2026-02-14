import sqlite3

conn = sqlite3.connect("Genomic_chatbot/genome.db")
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS motifs (
    motif_id TEXT PRIMARY KEY,
    tf TEXT,
    collection TEXT,
    datatype TEXT,
    quality TEXT,
    length INTEGER,
    consensus TEXT,
    gc_content REAL,
    ic_total REAL,
    ic_per_base REAL,
    num_words INTEGER,
    orientation TEXT,
    subtype_order INTEGER
);

CREATE TABLE IF NOT EXISTS tf_metadata (
    tf TEXT PRIMARY KEY,
    tfclass_id TEXT,
    superclass TEXT,
    class TEXT,
    family TEXT,
    subfamily TEXT,
    greco_db_tf TEXT
);

CREATE TABLE IF NOT EXISTS gene_info (
    tf TEXT,
    species TEXT,
    gene_symbol TEXT,
    uniprot_id TEXT,
    uniprot_ac TEXT,
    protein_name TEXT,
    hgnc TEXT,
    entrez TEXT,
    PRIMARY KEY (tf, species)
);

CREATE TABLE IF NOT EXISTS matrices (
    motif_id TEXT,
    matrix_type TEXT,
    matrix_json TEXT,
    PRIMARY KEY (motif_id, matrix_type)
);

CREATE TABLE IF NOT EXISTS metrics (
    motif_id TEXT,
    assay TEXT,
    context TEXT,
    metric_json TEXT,
    PRIMARY KEY (motif_id, assay, context)
);

CREATE TABLE IF NOT EXISTS thresholds (
    motif_id TEXT PRIMARY KEY,
    threshold_json TEXT
);

CREATE TABLE IF NOT EXISTS original_motif (
    motif_id TEXT PRIMARY KEY,
    origin TEXT,
    source_name TEXT,
    motif_datatype TEXT,
    species_counts TEXT,
    datatype_counts TEXT
);
""")
cur.executescript("""
-- Motif lookups
CREATE INDEX IF NOT EXISTS idx_motifs_tf
    ON motifs(tf);

CREATE INDEX IF NOT EXISTS idx_motifs_id
    ON motifs(motif_id);

CREATE INDEX IF NOT EXISTS idx_motifs_consensus
    ON motifs(consensus);

-- Metrics lookups
CREATE INDEX IF NOT EXISTS idx_metrics_assay
    ON metrics(assay);

CREATE INDEX IF NOT EXISTS idx_metrics_motif_assay
    ON metrics(motif_id, assay);
""")


conn.commit()
conn.close()
