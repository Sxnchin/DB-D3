#!/usr/bin/env python3
"""
Run All Tests Script
Executes all test scripts in sequence and provides summary
"""

import subprocess
import sys
import time

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(message):
    print(f"\n{Colors.CYAN}{Colors.BOLD}{'=' * 80}")
    print(f"{message}")
    print(f"{'=' * 80}{Colors.END}\n")

def print_success(message):
    print(f"{Colors.GREEN} Success {message}{Colors.END}")

def print_error(message):
    print(f"{Colors.RED} Error {message}{Colors.END}")

def print_info(message):
    print(f"{Colors.YELLOW} Info {message}{Colors.END}")

def run_test(script_name, description):
    """Run a test script and return success status"""
    print_header(f"Running: {description}")
    print_info(f"Executing: python {script_name}")
    print()
    
    try:
        result = subprocess.run(
            ['python', script_name],
            capture_output=False,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        if result.returncode == 0:
            print_success(f"{description} - PASSED")
            return True
        else:
            print_error(f"{description} - FAILED (Exit code: {result.returncode})")
            return False
            
    except subprocess.TimeoutExpired:
        print_error(f"{description} - TIMEOUT (exceeded 2 minutes)")
        return False
    except FileNotFoundError:
        print_error(f"{description} - FILE NOT FOUND ({script_name})")
        return False
    except Exception as e:
        print_error(f"{description} - ERROR: {str(e)}")
        return False

def check_api_running():
    """Check if Flask API is running"""
    import requests
    try:
        response = requests.get('http://localhost:5000/api/content', timeout=5)
        return True
    except:
        return False

def main():
    print_header("STREAMING SERVICE - COMPREHENSIVE TEST SUITE")
    
    print("This script will run all test suites in sequence:")
    print("  1. Admin Service Tests")
    print("  2. User Workflow Tests")
    print()
    
    # Check if API is running
    print_info("Checking if API server is running...")
    if not check_api_running():
        print_error("API server is not running!")
        print()
        print("Please start the Flask server in a separate terminal:")
        print(f"  {Colors.CYAN}python app.py{Colors.END}")
        print()
        return 1
    
    print_success("API server is running")
    print()
    
    # Wait a moment
    time.sleep(1)
    
    # Run tests
    tests = [
        ('test_admin_service.py', 'Admin Service Tests'),
        ('test_user_workflow.py', 'User Workflow Tests'),
    ]
    
    results = {}
    
    for script, description in tests:
        success = run_test(script, description)
        results[description] = success
        
        # Pause between tests
        if script != tests[-1][0]:
            print()
            print_info("Pausing 2 seconds before next test...")
            time.sleep(2)
    
    # Print summary
    print_header("TEST SUITE SUMMARY")
    
    all_passed = True
    for description, success in results.items():
        if success:
            print_success(f"{description}: PASSED")
        else:
            print_error(f"{description}: FAILED")
            all_passed = False
    
    print()
    if all_passed:
        print(f"{Colors.GREEN}{Colors.BOLD}{'=' * 80}")
        print(f"ALL TESTS PASSED!")
        print(f"{'=' * 80}{Colors.END}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}{'=' * 80}")
        print(f"SOME TESTS FAILED!")
        print(f"{'=' * 80}{Colors.END}")
        print()
        print("Check the output above for details on failed tests.")
        return 1

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print()
        print_error("Tests interrupted by user")
        sys.exit(1)