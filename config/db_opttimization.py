from django.db import connection
from django.core.management import call_command


def analyze_queries():
    """Analyze slow queries"""
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT query, calls, total_time, mean_time
            FROM pg_stat_statements
            ORDER BY mean_time DESC
            LIMIT 20;
        """)
        slow_queries = cursor.fetchall()

    return slow_queries


def create_partition_tables():
    """Create table partitions for large tables (optional)"""
    with connection.cursor() as cursor:
        # Create monthly partitions for applications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications_2024_01 PARTITION OF jobs_application
            FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
        """)
