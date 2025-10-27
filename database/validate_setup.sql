-- ============================================================================
-- Training Management System Database Validation Script
-- Quick validation queries to ensure setup is correct
-- ============================================================================

-- Check if all required tables exist
SELECT 
    'Tables Check' as validation_type,
    COUNT(*) as found_count,
    7 as expected_count,
    CASE WHEN COUNT(*) = 7 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'training_programs',
    'training_assignments', 
    'training_documents',
    'training_modules',
    'training_prerequisites',
    'training_assignment_history',
    'training_session_logs'
);

-- Check if views exist
SELECT 
    'Views Check' as validation_type,
    COUNT(*) as found_count,
    2 as expected_count,
    CASE WHEN COUNT(*) = 2 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM information_schema.views 
WHERE table_schema = 'public' 
AND table_name IN ('training_dashboard_stats', 'program_statistics');

-- Check if enums exist
SELECT 
    'Enums Check' as validation_type,
    COUNT(*) as found_count,
    5 as expected_count,
    CASE WHEN COUNT(*) = 5 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM pg_type 
WHERE typname IN (
    'training_type',
    'program_status', 
    'assignment_status',
    'document_type',
    'document_category'
);

-- Check sample data
SELECT 
    'Sample Data' as validation_type,
    COUNT(*) as found_count,
    4 as expected_count,
    CASE WHEN COUNT(*) >= 4 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM training_programs;

-- Test dashboard view functionality
SELECT 
    'Dashboard View' as validation_type,
    CASE 
        WHEN total_programs IS NOT NULL 
        AND active_assignments IS NOT NULL 
        AND compliance_rate IS NOT NULL 
        THEN 1 
        ELSE 0 
    END as found_count,
    1 as expected_count,
    CASE 
        WHEN total_programs IS NOT NULL 
        AND active_assignments IS NOT NULL 
        AND compliance_rate IS NOT NULL 
        THEN '✅ PASS' 
        ELSE '❌ FAIL' 
    END as status
FROM training_dashboard_stats;

-- Check indexes exist
SELECT 
    'Indexes Check' as validation_type,
    COUNT(*) as found_count,
    10 as expected_count,
    CASE WHEN COUNT(*) >= 10 THEN '✅ PASS' ELSE '❌ FAIL' END as status
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename LIKE 'training_%';

-- Summary of database structure
SELECT '=== DATABASE STRUCTURE SUMMARY ===' as summary;

SELECT 
    t.table_name,
    COUNT(c.column_name) as column_count,
    STRING_AGG(c.column_name, ', ' ORDER BY c.ordinal_position) as columns
FROM information_schema.tables t
LEFT JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_schema = 'public' 
AND t.table_name LIKE 'training_%'
GROUP BY t.table_name
ORDER BY t.table_name;

-- Test data samples
SELECT '=== SAMPLE DATA ===' as sample_data;

SELECT 
    id,
    title,
    type,
    duration,
    status,
    created_at
FROM training_programs
ORDER BY created_at
LIMIT 5;

-- Test dashboard statistics
SELECT '=== DASHBOARD STATISTICS ===' as dashboard;

SELECT * FROM training_dashboard_stats;

-- Performance check - ensure queries run quickly
SELECT '=== PERFORMANCE CHECK ===' as performance;

EXPLAIN (ANALYZE, BUFFERS) 
SELECT p.title, COUNT(a.id) as assignments
FROM training_programs p
LEFT JOIN training_assignments a ON p.id = a.program_id
GROUP BY p.id, p.title;

-- Final validation summary
SELECT '=== FINAL VALIDATION RESULT ===' as final_result;

WITH validation_results AS (
    SELECT 'Tables' as check_type, 
           CASE WHEN (SELECT COUNT(*) FROM information_schema.tables 
                     WHERE table_schema = 'public' AND table_name LIKE 'training_%') >= 7 
           THEN 1 ELSE 0 END as passed
    UNION ALL
    SELECT 'Views',
           CASE WHEN (SELECT COUNT(*) FROM information_schema.views 
                     WHERE table_schema = 'public' AND table_name IN ('training_dashboard_stats', 'program_statistics')) = 2
           THEN 1 ELSE 0 END
    UNION ALL
    SELECT 'Sample Data',
           CASE WHEN (SELECT COUNT(*) FROM training_programs) >= 4
           THEN 1 ELSE 0 END
    UNION ALL
    SELECT 'Dashboard View',
           CASE WHEN (SELECT total_programs FROM training_dashboard_stats) IS NOT NULL
           THEN 1 ELSE 0 END
)
SELECT 
    SUM(passed) as checks_passed,
    COUNT(*) as total_checks,
    ROUND(SUM(passed)::numeric / COUNT(*) * 100, 1) as success_rate,
    CASE 
        WHEN SUM(passed) = COUNT(*) THEN '🎉 ALL CHECKS PASSED - DATABASE READY FOR PRODUCTION!'
        WHEN SUM(passed) >= COUNT(*) * 0.8 THEN '⚠️  MOSTLY READY - CHECK FAILED ITEMS'
        ELSE '❌ SETUP INCOMPLETE - REVIEW ERRORS'
    END as overall_status
FROM validation_results;