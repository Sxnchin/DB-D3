#!/usr/bin/env python3
"""Tests complete user workflow: register, profile creation, content browsing, wishlist, and viewing history."""

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

    # Fetch available subscriptions
    print('[TEST] Fetching available subscriptions')
    try:
        r = requests.get(f'{API_BASE}/api/subscriptions', timeout=5)
    except Exception as e:
        print(f'✗ ERROR: Could not connect to API: {e}')
        return 2

    if r.status_code != 200:
        print(f'Failed to fetch subscriptions (status: {r.status_code}) - {r.text}')
        return 2

    subscriptions = r.json()
    if not subscriptions:
        print('No subscriptions available')
        return 2

    subscription_id = subscriptions[0].get('subscription_id')
    print(f' Info : Using subscription ID: {subscription_id}')

    # Register a new user
    print('\n[TEST] Registering new user account')
    email = f'testuser{int(time.time())}@example.com'
    password = 'SecurePass123!'
    payload = {'email': email, 'password': password, 'subscription_id': subscription_id}

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
    if not items:
        print(' Error : No content available to test wishlist/history')
        return 2

    # Choose a content item to test wishlist and viewing history
    first_item = items[0]
    content_id = None
    if isinstance(first_item, dict):
        content_id = first_item.get('content_id') or first_item.get('id')
    else:
        try:
            content_id = first_item[0].get('content_id')
        except Exception:
            content_id = None

    if not content_id:
        print(' Error : Could not determine a content_id from content list')
        return 2

    # --- Wishlist: add item, verify present, then remove ---
    print('\n[TEST] Wishlist: add and verify')
    r = requests.post(f'{API_BASE}/api/profiles/{profile_id}/wishlist/{content_id}', headers=headers, timeout=5)
    if r.status_code not in (200, 201):
        print(f' Error : Failed to add to wishlist (status: {r.status_code}) - {r.text}')
        return 2

    r = requests.get(f'{API_BASE}/api/profiles/{profile_id}/wishlist', headers=headers, timeout=5)
    if r.status_code != 200:
        print(f' Error : Failed to fetch wishlist (status: {r.status_code}) - {r.text}')
        return 2

    wishlist = r.json()
    try:
        found = any(int(w.get('content_id')) == int(content_id) for w in wishlist)
    except Exception:
        found = any(str(w.get('content_id')) == str(content_id) for w in wishlist)

    if not found:
        print(' Error : Content not found in wishlist after adding')
        return 2

    print(' Info : Wishlist contains the added content')

    # --- Viewing history: update and verify ---
    print('\n[TEST] Viewing History: update and verify')
    last_ts = int(time.time())
    r = requests.put(
        f'{API_BASE}/api/profiles/{profile_id}/history/{content_id}',
        headers=headers,
        json={'last_timestamp': last_ts},
        timeout=5
    )
    if r.status_code != 200:
        print(f' Error : Failed to update viewing history (status: {r.status_code}) - {r.text}')
        return 2

    r = requests.get(f'{API_BASE}/api/profiles/{profile_id}/history/{content_id}', headers=headers, timeout=5)
    if r.status_code != 200:
        print(f' Error : Failed to fetch viewing history item (status: {r.status_code}) - {r.text}')
        return 2

    history_item = r.json()
    returned_ts = history_item.get('last_timestamp')
    try:
        returned_int = int(float(returned_ts))
    except Exception:
        try:
            returned_int = int(returned_ts)
        except Exception:
            returned_int = None

    if returned_int != last_ts:
        print(f' Error : Viewing history timestamp mismatch (sent: {last_ts}, got: {returned_ts})')
        return 2

    print(' Info : Viewing history updated and verified')
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
