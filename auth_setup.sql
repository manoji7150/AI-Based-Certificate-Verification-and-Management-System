-- 1. Add password column to students table (if not exists)
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='students' AND column_name='password') THEN
        ALTER TABLE students ADD COLUMN password TEXT DEFAULT 'password123';
    END IF;
END $$;

-- 2. Create Staff Table (DROP first to ensure correct columns)
DROP TABLE IF EXISTS staff CASCADE;

CREATE TABLE staff (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    full_name TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Example: Insert a staff account
INSERT INTO staff (email, password, full_name)
VALUES ('staff@college.com', 'admin123', 'Staff Member');

-- 4. Enable RLS and add basic policies for staff table
ALTER TABLE staff ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Allow all for staff" ON staff FOR ALL USING (true) WITH CHECK (true);
GRANT ALL ON staff TO anon, authenticated;
