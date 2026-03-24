-- ==========================================
-- SUPER FIX: DATABASE & STORAGE PERMISSIONS
-- ==========================================

-- Part 1: Fix Database Table Policies
-- Drop existing policies to ensure a clean slate
DROP POLICY IF EXISTS "Allow all students" ON students;
DROP POLICY IF EXISTS "Allow all certificates" ON certificates;

-- Create highly permissive policies for the app
CREATE POLICY "Allow all students" ON students FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);
CREATE POLICY "Allow all certificates" ON certificates FOR ALL TO anon, authenticated USING (true) WITH CHECK (true);

-- Ensure anon role can actually use the tables
GRANT ALL ON students TO anon, authenticated;
GRANT ALL ON certificates TO anon, authenticated;


-- Part 2: Fix Storage Bucket Policies
-- This is where the 403 error is most likely coming from

-- Ensure bucket is public
UPDATE storage.buckets SET public = true WHERE id = 'certificates';

-- Drop existing storage policies
DROP POLICY IF EXISTS "Allow Public Selection" ON storage.objects;
DROP POLICY IF EXISTS "Allow Public Insertion" ON storage.objects;
DROP POLICY IF EXISTS "Allow Public Update" ON storage.objects;
DROP POLICY IF EXISTS "Allow Public Delete" ON storage.objects;
DROP POLICY IF EXISTS "Allow Anon to view buckets" ON storage.buckets;

-- 1. Grant Select on buckets so the app can "see" it
CREATE POLICY "Allow Anon to view buckets"
ON storage.buckets FOR SELECT
TO anon, authenticated
USING ( true );

-- 2. Allow Selection/Downloading of files
CREATE POLICY "Allow Public Selection"
ON storage.objects FOR SELECT
TO anon, authenticated
USING ( bucket_id = 'certificates' );

-- 3. Allow Insertion/Uploading of files (CRITICAL FOR 403 FIX)
CREATE POLICY "Allow Public Insertion"
ON storage.objects FOR INSERT
TO anon, authenticated
WITH CHECK ( bucket_id = 'certificates' );

-- 4. Allow Updating (Optional)
CREATE POLICY "Allow Public Update"
ON storage.objects FOR UPDATE
TO anon, authenticated
USING ( bucket_id = 'certificates' )
WITH CHECK ( bucket_id = 'certificates' );

-- 5. Grant internal schema usage to anon role
GRANT USAGE ON SCHEMA storage TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA storage TO anon, authenticated;
