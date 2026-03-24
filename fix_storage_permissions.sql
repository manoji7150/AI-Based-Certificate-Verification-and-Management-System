-- 1. Ensure the bucket exists
INSERT INTO storage.buckets (id, name, public)
SELECT 'certificates', 'certificates', true
WHERE NOT EXISTS (
    SELECT 1 FROM storage.buckets WHERE id = 'certificates'
);

-- 2. Clear any old/broken storage policies for this bucket
-- We use DROP POLICY on the specific tables
DROP POLICY IF EXISTS "Allow Public Selection" ON storage.objects;
DROP POLICY IF EXISTS "Allow Public Insertion" ON storage.objects;
DROP POLICY IF EXISTS "Allow Public Update" ON storage.objects;
DROP POLICY IF EXISTS "Allow Anon to view buckets" ON storage.buckets;

-- 3. Create CLEAN policies for storage.objects
-- This allows anyone (anon) to upload and view certificates

-- ALLOW DOWNLOADS/SELECTION
CREATE POLICY "Allow Public Selection"
ON storage.objects FOR SELECT
TO anon, authenticated
USING ( bucket_id = 'certificates' );

-- ALLOW UPLOADS
CREATE POLICY "Allow Public Insertion"
ON storage.objects FOR INSERT
TO anon, authenticated
WITH CHECK ( bucket_id = 'certificates' );

-- ALLOW UPDATES (Optional, used for overwriting)
CREATE POLICY "Allow Public Update"
ON storage.objects FOR UPDATE
TO anon, authenticated
USING ( bucket_id = 'certificates' );


-- 4. CRITICAL: Allow the 'anon' role to see the bucket existence
-- This fixes the "Bucket not found" error in the app UI
CREATE POLICY "Allow Anon to view buckets"
ON storage.buckets FOR SELECT
TO anon, authenticated
USING ( true );
