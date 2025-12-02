#!/usr/bin/env python3
"""
Simple Admin Service Test Script
This script verifies basic admin endpoints: login and list subscriptions.
"""

import os
import sys
import time
import requests

API_BASE = os.environ.get('API_BASE', 'http://localhost:5000')


def print_header(msg):
    print('\n' + '=' * 80)
    print(msg)
    print('=' * 80 + '\n')


def main():
    print_header('STREAMING SERVICE - ADMIN SERVICE TEST SCRIPT')

    # Admin login
    print('[TEST] Admin Authentication')
    login_payload = {
        'username': os.environ.get('ADMIN_USER', 'admin'),
        'password': os.environ.get('ADMIN_PASS', 'admin123')
    }

    try:
        r = requests.post(f'{API_BASE}/api/admin/login', json=login_payload, timeout=5)
    except Exception as e:
        print(f'✗ ERROR: Could not connect to API: {e}')
        return 2

    if r.status_code != 200:
        print(f'✗ Admin login failed (status: {r.status_code}) - {r.text}')
        return 2

    data = r.json()
    token = data.get('token')
    if not token:
        print('✗ Admin login response missing token')
        return 2

    print('✓ Admin logged in successfully')
    print(f'ℹ Admin ID: {data.get("admin_id")}')

    # Get subscriptions
    print('\n[TEST] Subscription Plan Management')
    headers = {'Authorization': f'Bearer {token}'}
    r = requests.get(f'{API_BASE}/api/admin/subscriptions', headers=headers, timeout=5)
    if r.status_code != 200:
        print(f'✗ Failed to retrieve subscriptions (status: {r.status_code}) - {r.text}')
        return 2

    subs = r.json()
    print(f'✓ Retrieved {len(subs)} subscription plans')

    # Create a temporary subscription (POST)
    payload = {'name': 'Enterprise', 'max_profiles': 10, 'monthly_price': 44.99}
    r = requests.post(f'{API_BASE}/api/admin/subscriptions', headers=headers, json=payload, timeout=5)
    if r.status_code != 200 and r.status_code != 201:
        print(f'✗ Failed to create subscription (status: {r.status_code})')
        return 2

    created_id = r.json().get('subscription_id')
    print(f'✓ Created subscription Enterprise (ID: {created_id})')

    # Clean up: delete the subscription we created
    r = requests.delete(f'{API_BASE}/api/admin/subscriptions/{created_id}', headers=headers, timeout=5)
    if r.status_code != 200:
        print(f'✗ Failed to delete temporary subscription (status: {r.status_code})')
        # Not fatal; continue
    else:
        print('✓ Deleted temporary subscription')

    print('\nALL ADMIN TESTS COMPLETED SUCCESSFULLY!')
    return 0


if __name__ == '__main__':
    try:
        rc = main()
        sys.exit(rc)
    except KeyboardInterrupt:
        print('\nTests interrupted by user')
        sys.exit(1)
