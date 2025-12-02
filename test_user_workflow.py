#!/usr/bin/env python3
"""
Simple User Workflow Test Script
This script simulates a minimal user flow: register, login, create profile, and fetch content.
"""

import os
import sys
import requests
import time
import random

API_BASE = os.environ.get('API_BASE', 'http://localhost:5000')


def print_header(msg):
    print('\n' + '=' * 80)
    print(msg)
    print('=' * 80 + '\n')


def main():
    print_header('STREAMING SERVICE - COMPLETE USER WORKFLOW TEST')

    # Register a new user
    print('[TEST] Registering new user account')
    email = f'testuser{int(time.time())}@example.com'
    password = 'SecurePass123!'
    payload = {'email': email, 'password': password}

    try:
        r = requests.post(f'{API_BASE}/api/auth/register', json=payload, timeout=5)
    except Exception as e:
        print(f'✗ ERROR: Could not connect to API: {e}')
        return 2

    if r.status_code != 201:
        print(f'User registration failed (status: {r.status_code}) - {r.text}')
        return 2

    data = r.json()
    token = data.get('token')
    if not token:
        print('Registration response missing token')
        return 2

    print(' User registered successfully')
    print(f' Info Email: {email}')
    print(f' Info Account ID: {data.get("account_id")}')

    # Create profile
    print('\n[TEST] Creating user profile')
    headers = {'Authorization': f'Bearer {token}'}
    payload = {'name': 'John', 'age_rating_pref': 'PG-13'}
    r = requests.post(f'{API_BASE}/api/profiles', headers=headers, json=payload, timeout=5)
    if r.status_code not in (200, 201):
        print(f' Error : Failed to create profile (status: {r.status_code}) - {r.text}')
        return 2

    profile = r.json()
    profile_id = profile.get('profile_id') if isinstance(profile, dict) else profile[0].get('profile_id')
    print(f' Info : Created profile "John" (ID: {profile_id})')

    # Browse content
    print('\n[TEST] Content Browsing')
    r = requests.get(f'{API_BASE}/api/content', timeout=5)
    if r.status_code != 200:
        print(f' Error : Failed to fetch content (status: {r.status_code}) - {r.text}')
        return 2

    items = r.json()
    print(f' Info : Retrieved {len(items)} content items')
    print('\n Info : ALL USER WORKFLOW TESTS COMPLETED SUCCESSFULLY!')
    print('\nTest User Credentials:')
    print(f'  Email: {email}')
    print(f'  Password: {password}')
    return 0


if __name__ == '__main__':
    try:
        rc = main()
        sys.exit(rc)
    except KeyboardInterrupt:
        print('\nTests interrupted by user')
        sys.exit(1)
