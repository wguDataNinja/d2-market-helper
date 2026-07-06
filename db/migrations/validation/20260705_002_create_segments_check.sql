-- Validate segments table and seed data
SELECT segment_slug, display_name, enabled FROM app.segments ORDER BY segment_slug;

-- Expect exactly 4 segments
SELECT COUNT(*) = 4 AS correct_segment_count FROM app.segments;
