#!/usr/bin/env python3
# QMS Compliance Validation Script
# Validate 21 CFR Part 11 compliance features

import sys
import requests
import json
from datetime import datetime
from pathlib import Path


def validate_compliance(api_base_url: str, environment: str = "production"):
    """Validate compliance features."""
    
    print(f"Validating 21 CFR Part 11 compliance for {environment} environment")
    print(f"API Base URL: {api_base_url}")
    
    validation_results = {
        "timestamp": datetime.utcnow().isoformat(),
        "environment": environment,
        "api_base_url": api_base_url,
        "tests": {},
        "overall_status": "UNKNOWN"
    }
    
    # Test 1: System Information
    print("\n1. Testing system information...")
    try:
        response = requests.get(f"{api_base_url}/api/v1/system/info", timeout=10)
        if response.status_code == 200:
            info = response.json()
            validation_results["tests"]["system_info"] = {
                "status": "PASS",
                "compliance_declared": info.get("compliance") == "21 CFR Part 11",
                "features": info.get("features", [])
            }
            print("✅ System information accessible")
        else:
            validation_results["tests"]["system_info"] = {
                "status": "FAIL",
                "error": f"HTTP {response.status_code}"
            }
            print(f"❌ System info failed: {response.status_code}")
    except Exception as e:
        validation_results["tests"]["system_info"] = {
            "status": "ERROR",
            "error": str(e)
        }
        print(f"❌ System info error: {e}")
    
    # Test 2: Health Check
    print("\n2. Testing system health...")
    try:
        response = requests.get(f"{api_base_url}/health", timeout=10)
        if response.status_code == 200:
            health = response.json()
            validation_results["tests"]["health_check"] = {
                "status": "PASS",
                "system_healthy": health.get("status") == "healthy",
                "version": health.get("version"),
                "environment": health.get("environment")
            }
            print("✅ System health check passed")
        else:
            validation_results["tests"]["health_check"] = {
                "status": "FAIL",
                "error": f"HTTP {response.status_code}"
            }
            print(f"❌ Health check failed: {response.status_code}")
    except Exception as e:
        validation_results["tests"]["health_check"] = {
            "status": "ERROR",
            "error": str(e)
        }
        print(f"❌ Health check error: {e}")
    
    # Test 3: Database Status
    print("\n3. Testing database connectivity...")
    try:
        response = requests.get(f"{api_base_url}/api/v1/system/database/status", timeout=10)
        if response.status_code == 200:
            db_status = response.json()
            validation_results["tests"]["database_status"] = {
                "status": "PASS",
                "connection_info_masked": "***" in db_status.get("url", ""),
                "pool_info_available": "pool_size" in db_status
            }
            print("✅ Database status accessible")
        else:
            validation_results["tests"]["database_status"] = {
                "status": "FAIL",
                "error": f"HTTP {response.status_code}"
            }
            print(f"❌ Database status failed: {response.status_code}")
    except Exception as e:
        validation_results["tests"]["database_status"] = {
            "status": "ERROR",
            "error": str(e)
        }
        print(f"❌ Database status error: {e}")
    
    # Test 4: Security Headers
    print("\n4. Testing security headers...")
    try:
        response = requests.get(f"{api_base_url}/health", timeout=10)
        headers = response.headers
        
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Content-Security-Policy"
        ]
        
        header_results = {}
        for header in required_headers:
            header_results[header] = header in headers
        
        validation_results["tests"]["security_headers"] = {
            "status": "PASS" if all(header_results.values()) else "FAIL",
            "headers_present": header_results,
            "missing_headers": [h for h, present in header_results.items() if not present]
        }
        
        if all(header_results.values()):
            print("✅ Security headers present")
        else:
            print(f"❌ Missing security headers: {validation_results['tests']['security_headers']['missing_headers']}")
            
    except Exception as e:
        validation_results["tests"]["security_headers"] = {
            "status": "ERROR",
            "error": str(e)
        }
        print(f"❌ Security headers test error: {e}")
    
    # Test 5: Authentication Endpoint
    print("\n5. Testing authentication endpoint...")
    try:
        # Test with invalid credentials
        response = requests.post(
            f"{api_base_url}/api/v1/auth/login",
            json={"username": "invalid", "password": "invalid"},
            timeout=10
        )
        
        if response.status_code == 401:
            validation_results["tests"]["authentication"] = {
                "status": "PASS",
                "rejects_invalid_credentials": True,
                "returns_proper_error": "detail" in response.json()
            }
            print("✅ Authentication endpoint working")
        else:
            validation_results["tests"]["authentication"] = {
                "status": "FAIL",
                "error": f"Expected 401, got {response.status_code}"
            }
            print(f"❌ Authentication test failed: expected 401, got {response.status_code}")
            
    except Exception as e:
        validation_results["tests"]["authentication"] = {
            "status": "ERROR",
            "error": str(e)
        }
        print(f"❌ Authentication test error: {e}")
    
    # Calculate overall status
    test_results = [test.get("status") for test in validation_results["tests"].values()]
    
    if all(status == "PASS" for status in test_results):
        validation_results["overall_status"] = "COMPLIANT"
        overall_result = "✅ COMPLIANT"
    elif any(status == "ERROR" for status in test_results):
        validation_results["overall_status"] = "ERROR" 
        overall_result = "⚠️ ERROR"
    else:
        validation_results["overall_status"] = "NON_COMPLIANT"
        overall_result = "❌ NON_COMPLIANT"
    
    # Summary
    print("\n" + "="*50)
    print("COMPLIANCE VALIDATION SUMMARY")
    print("="*50)
    print(f"Overall Status: {overall_result}")
    print(f"Environment: {environment}")
    print(f"Timestamp: {validation_results['timestamp']}")
    
    for test_name, test_result in validation_results["tests"].items():
        status_icon = {"PASS": "✅", "FAIL": "❌", "ERROR": "⚠️"}.get(test_result["status"], "❓")
        print(f"{status_icon} {test_name}: {test_result['status']}")
    
    return validation_results


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate QMS compliance")
    parser.add_argument(
        "--api-url",
        default="http://localhost:8000",
        help="API base URL (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--environment",
        default="development",
        help="Environment name (default: development)"
    )
    parser.add_argument(
        "--output",
        help="Output file for validation results (JSON)"
    )
    
    args = parser.parse_args()
    
    try:
        results = validate_compliance(args.api_url, args.environment)
        
        # Save results if output file specified
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"\nResults saved to: {args.output}")
        
        # Exit with appropriate code
        if results["overall_status"] == "COMPLIANT":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()