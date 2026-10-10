-- Annex C: Fixed Schema (Required Tables)
-- Must not rename or remove these columns

CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY CHECK (student_id GLOB 'S[0-9][0-9][0-9][0-9]'),
    full_name TEXT NOT NULL,
    programme TEXT NOT NULL,
    batch_year INTEGER NOT NULL,
    current_semester INTEGER NOT NULL CHECK (current_semester BETWEEN 1 AND 10),
    cgpa REAL NOT NULL CHECK (cgpa BETWEEN 0 AND 10),
    active_backlogs INTEGER NOT NULL CHECK (active_backlogs >= 0)
);

CREATE TABLE IF NOT EXISTS courses (
    course_code TEXT PRIMARY KEY,
    course_name TEXT NOT NULL,
    programme TEXT NOT NULL,
    semester INTEGER NOT NULL,
    credits INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS attendance (
    student_id TEXT NOT NULL REFERENCES students(student_id),
    course_code TEXT NOT NULL REFERENCES courses(course_code),
    classes_held INTEGER NOT NULL CHECK (classes_held > 0),
    classes_attended INTEGER NOT NULL CHECK (classes_attended >= 0 AND classes_attended <= classes_held),
    PRIMARY KEY (student_id, course_code)
);

CREATE TABLE IF NOT EXISTS results (
    student_id TEXT NOT NULL REFERENCES students(student_id),
    course_code TEXT NOT NULL REFERENCES courses(course_code),
    exam_session TEXT NOT NULL,
    exam_type TEXT NOT NULL CHECK (exam_type IN ('REGULAR', 'SUPPLEMENTARY')),
    internal_marks INTEGER,
    external_marks INTEGER,
    total_marks INTEGER,
    max_marks INTEGER NOT NULL,
    result TEXT NOT NULL CHECK (result IN ('PASS', 'FAIL', 'ABSENT', 'DETAINED')),
    PRIMARY KEY (student_id, course_code, exam_session, exam_type)
);

CREATE TABLE IF NOT EXISTS rule_registry (
    rule_id TEXT PRIMARY KEY,
    description TEXT,
    parameter TEXT NOT NULL,
    operator TEXT NOT NULL,
    value TEXT NOT NULL,
    scope_programmes TEXT NOT NULL DEFAULT 'ALL',
    scope_batches TEXT NOT NULL DEFAULT 'ALL',
    effective_from TEXT NOT NULL,
    effective_to TEXT,
    source_doc_id TEXT NOT NULL,
    source_section TEXT NOT NULL,
    authority_level INTEGER NOT NULL,
    supersedes TEXT,
    status TEXT NOT NULL DEFAULT 'seed' CHECK (status IN ('seed', 'auto_extracted', 'verified'))
);

-- Extra Tables (Our additions)

CREATE TABLE IF NOT EXISTS source_register (
    doc_id TEXT PRIMARY KEY,
    title TEXT,
    issuer TEXT,
    authority_level INTEGER,
    doc_type TEXT,
    version TEXT,
    effective_from TEXT,
    effective_to TEXT,
    supersedes TEXT,
    scope_programmes TEXT,
    scope_batches TEXT,
    provenance TEXT,
    retrieved_on TEXT,
    synthetic TEXT,
    content_sha256 TEXT,
    ingested_at TEXT,
    chunk_count INTEGER,
    rule_count INTEGER,
    status TEXT
);

CREATE TABLE IF NOT EXISTS audit_log (
    trace_id TEXT PRIMARY KEY,
    ts TEXT NOT NULL,
    student_id TEXT,
    answer_type TEXT,
    record_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ingest_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT,
    ts TEXT,
    status TEXT,
    warnings_json TEXT
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_students_programme ON students(programme);
CREATE INDEX IF NOT EXISTS idx_students_batch ON students(batch_year);
CREATE INDEX IF NOT EXISTS idx_attendance_student ON attendance(student_id);
CREATE INDEX IF NOT EXISTS idx_results_student ON results(student_id);
CREATE INDEX IF NOT EXISTS idx_rules_parameter ON rule_registry(parameter);
CREATE INDEX IF NOT EXISTS idx_rules_effective ON rule_registry(effective_from);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON audit_log(ts);
