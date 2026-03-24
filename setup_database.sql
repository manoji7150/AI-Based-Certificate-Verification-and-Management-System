-- IMPORTANT: This will drop existing tables and dependent objects (like views/constraints)
-- then recreate them with the correct schema
DROP TABLE IF EXISTS certificates CASCADE;
DROP TABLE IF EXISTS students CASCADE;

-- 1. Create Students Table
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    roll_number TEXT UNIQUE NOT NULL,
    full_name TEXT NOT NULL,
    email TEXT,
    department TEXT,
    gpa FLOAT DEFAULT 0.0,
    points INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 2. Create Certificates Table
CREATE TABLE certificates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID REFERENCES students(id),
    student_name TEXT,
    student_email TEXT,
    roll_number TEXT,
    department TEXT,
    event_name TEXT NOT NULL,
    event_type TEXT NOT NULL,
    marks INTEGER DEFAULT 0,
    achievement_level TEXT,
    verification_score INTEGER DEFAULT 0,
    verification_status TEXT DEFAULT 'NOT VALID CERTIFICATE',
    file_url TEXT NOT NULL,
    status TEXT DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Enable RLS
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE certificates ENABLE ROW LEVEL SECURITY;

-- 4. Create Simple Policies
CREATE POLICY "Allow all students" ON students FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all certificates" ON certificates FOR ALL USING (true) WITH CHECK (true);
