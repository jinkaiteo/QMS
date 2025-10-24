# QMS Logging Configuration
# Phase 1: Structured logging for compliance and audit

import logging
import logging.config
import structlog
import sys
from pathlib import Path
from typing import Any, Dict
import json
from datetime import datetime

from app.core.config import settings


def setup_logging():
    """Setup structured logging for QMS application"""
    
    # Ensure log directory exists
    import os
    if os.getenv("ENVIRONMENT", "development") == "development":
        log_dir = Path("logs")  # Use local logs directory for development
    else:
        log_dir = Path("/app/logs")
    
    try:
        log_dir.mkdir(exist_ok=True, parents=True)
    except (PermissionError, OSError):
        # Fallback to current directory if permission denied
        log_dir = Path(".")
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure standard logging
    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter"
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "standard",
                "stream": sys.stdout
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "json",
                "filename": "logs/qms.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5
            },
            "audit_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/audit.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10  # Keep more audit logs
            },
            "security_file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "formatter": "json",
                "filename": "logs/security.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 10
            }
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": settings.LOG_LEVEL,
                "propagate": False
            },
            "qms.audit": {
                "handlers": ["audit_file"],
                "level": "INFO",
                "propagate": False
            },
            "qms.security": {
                "handlers": ["security_file", "console"],
                "level": "INFO",
                "propagate": False
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False
            },
            "sqlalchemy.engine": {
                "handlers": ["file"],
                "level": "WARNING",
                "propagate": False
            }
        }
    }
    
    logging.config.dictConfig(logging_config)


class ComplianceLogger:
    """Specialized logger for pharmaceutical compliance requirements"""
    
    def __init__(self):
        self.audit_logger = logging.getLogger("qms.audit")
        self.security_logger = logging.getLogger("qms.security")
        self.main_logger = logging.getLogger("qms.main")
    
    def log_user_action(
        self,
        user_id: int,
        username: str,
        action: str,
        resource: str,
        details: Dict[str, Any] = None,
        ip_address: str = None,
        user_agent: str = None
    ):
        """Log user actions for 21 CFR Part 11 compliance"""
        audit_entry = {
            "event_type": "user_action",
            "user_id": user_id,
            "username": username,
            "action": action,
            "resource": resource,
            "timestamp": datetime.utcnow().isoformat(),
            "ip_address": ip_address,
            "user_agent": user_agent,
            "details": details or {}
        }
        
        self.audit_logger.info("User action logged", extra=audit_entry)
    
    def log_data_change(
        self,
        user_id: int,
        username: str,
        table_name: str,
        record_id: str,
        operation: str,
        old_values: Dict = None,
        new_values: Dict = None,
        reason: str = None
    ):
        """Log data changes for audit trail"""
        change_entry = {
            "event_type": "data_change",
            "user_id": user_id,
            "username": username,
            "table_name": table_name,
            "record_id": record_id,
            "operation": operation,
            "old_values": old_values,
            "new_values": new_values,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.audit_logger.info("Data change logged", extra=change_entry)
    
    def log_system_event(
        self,
        event_type: str,
        description: str,
        severity: str = "INFO",
        details: Dict[str, Any] = None
    ):
        """Log system events"""
        system_entry = {
            "event_type": "system_event",
            "description": description,
            "severity": severity,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        if severity.upper() == "ERROR":
            self.main_logger.error("System event", extra=system_entry)
        elif severity.upper() == "WARNING":
            self.main_logger.warning("System event", extra=system_entry)
        else:
            self.main_logger.info("System event", extra=system_entry)
    
    def log_security_event(
        self,
        event_type: str,
        user_id: int = None,
        username: str = None,
        ip_address: str = None,
        success: bool = True,
        details: Dict[str, Any] = None
    ):
        """Log security-related events"""
        security_entry = {
            "event_type": f"security_{event_type}",
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        if success:
            self.security_logger.info(f"Security event: {event_type}", extra=security_entry)
        else:
            self.security_logger.warning(f"Security failure: {event_type}", extra=security_entry)
    
    def log_document_event(
        self,
        user_id: int,
        username: str,
        document_id: int,
        document_number: str,
        action: str,
        version: str = None,
        details: Dict[str, Any] = None
    ):
        """Log document-related events for EDMS compliance"""
        doc_entry = {
            "event_type": "document_event",
            "user_id": user_id,
            "username": username,
            "document_id": document_id,
            "document_number": document_number,
            "action": action,
            "version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "details": details or {}
        }
        
        self.audit_logger.info(f"Document {action}", extra=doc_entry)
    
    def log_electronic_signature(
        self,
        user_id: int,
        username: str,
        document_id: int,
        signature_meaning: str,
        signature_hash: str,
        certificate_info: Dict[str, Any] = None
    ):
        """Log electronic signature events"""
        signature_entry = {
            "event_type": "electronic_signature",
            "user_id": user_id,
            "username": username,
            "document_id": document_id,
            "signature_meaning": signature_meaning,
            "signature_hash": signature_hash,
            "certificate_info": certificate_info or {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.audit_logger.info("Electronic signature applied", extra=signature_entry)


# Global compliance logger instance
compliance_logger = ComplianceLogger()


class AuditLogFormatter(logging.Formatter):
    """Custom formatter for audit logs to ensure compliance format"""
    
    def format(self, record):
        """Format log record for compliance requirements"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": getattr(record, 'module', None),
            "function": getattr(record, 'funcName', None),
            "line": getattr(record, 'lineno', None)
        }
        
        # Add extra fields if present
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 
                          'pathname', 'filename', 'module', 'exc_info',
                          'exc_text', 'stack_info', 'lineno', 'funcName',
                          'created', 'msecs', 'relativeCreated', 'thread',
                          'threadName', 'processName', 'process', 'getMessage']:
                log_entry[key] = value
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with proper configuration"""
    return logging.getLogger(name)


def get_audit_logger():
    """Get the global audit logger instance"""
    return AuditLogger()
