# QMS Database Configuration
# Phase 1: SQLAlchemy database setup with connection pooling

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
import logging
from typing import Generator

from app.core.config import settings

logger = logging.getLogger(__name__)

# Create database engine with connection pooling
engine = create_engine(
    str(settings.DATABASE_URL),
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,    # Recycle connections every 5 minutes
    pool_size=10,        # Connection pool size
    max_overflow=20,     # Max overflow connections
    echo=settings.DEBUG, # Log SQL queries in debug mode
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def set_search_path(dbapi_connection, connection_record):
    """Set the search path for the connection"""
    with dbapi_connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")


# Add event listener to set search path
event.listen(engine, "connect", set_search_path)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency to get database session
    Used with FastAPI's Depends()
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_context(user_id: int = None, ip_address: str = None) -> Generator[Session, None, None]:
    """
    Get database session with audit context for 21 CFR Part 11 compliance
    Sets application context variables for audit triggers
    """
    db = SessionLocal()
    try:
        # Set application context for audit triggers
        if user_id:
            db.execute(f"SET LOCAL app.current_user_id = '{user_id}'")
        if ip_address:
            db.execute(f"SET LOCAL app.client_ip = '{ip_address}'")
        
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def create_tables():
    """Create all tables in the database"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


class DatabaseManager:
    """Database management utilities"""
    
    @staticmethod
    def get_connection_info():
        """Get database connection information"""
        return {
            "url": str(settings.DATABASE_URL).replace(settings.POSTGRES_PASSWORD, "***"),
            "pool_size": engine.pool.size(),
            "checked_out": engine.pool.checkedout(),
            "overflow": engine.pool.overflow(),
            "checked_in": engine.pool.checkedin()
        }
    
    @staticmethod
    def health_check():
        """Comprehensive database health check"""
        try:
            db = SessionLocal()
            
            # Test basic connection
            result = db.execute("SELECT 1 as test").fetchone()
            
            # Test audit table (critical for compliance)
            audit_count = db.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0]
            
            # Test write capability
            db.execute("""
                INSERT INTO audit_logs (user_id, username, action, table_name, record_id, reason, is_system_action)
                VALUES (1, 'system', 'CREATE', 'health_check', 'test', 'Health check test', true)
            """)
            db.commit()
            
            db.close()
            
            return {
                "status": "healthy",
                "connection": "ok",
                "audit_logs_count": audit_count,
                "write_test": "ok"
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    @staticmethod
    def backup_database(backup_path: str = None):
        """Create database backup using pg_dump"""
        import subprocess
        import datetime
        
        if not backup_path:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = f"{settings.BACKUP_PATH}/qms_backup_{timestamp}.sql"
        
        try:
            # Build pg_dump command
            cmd = [
                "pg_dump",
                "-h", settings.POSTGRES_SERVER,
                "-p", settings.POSTGRES_PORT,
                "-U", settings.POSTGRES_USER,
                "-d", settings.POSTGRES_DB,
                "-f", backup_path,
                "--verbose",
                "--clean",
                "--if-exists",
                "--no-owner",
                "--no-privileges"
            ]
            
            # Set password via environment
            env = {"PGPASSWORD": settings.POSTGRES_PASSWORD}
            
            # Execute backup
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Database backup created: {backup_path}")
                return {"status": "success", "backup_path": backup_path}
            else:
                logger.error(f"Backup failed: {result.stderr}")
                return {"status": "failed", "error": result.stderr}
                
        except Exception as e:
            logger.error(f"Backup error: {e}")
            return {"status": "failed", "error": str(e)}


# Initialize database manager
db_manager = DatabaseManager()