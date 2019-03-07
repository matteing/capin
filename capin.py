#!/usr/bin/env python3
import requests
from requests_html import HTMLSession
import time
from configparser import SafeConfigParser
from getpass import getpass

# Init config file
config = SafeConfigParser()
config.read('config.ini')

if 'auth' not in config.sections() or not config['auth'].get('username', False) or not config['auth'].get('password', False):
	print("One-time setup - please enter your student number and password:")
	config.add_section('auth')
	config.set('auth', 'username', input("Student #: "))
	config.set('auth', 'password', getpass("Password: "))

	with open('config.ini', 'w') as f:
		config.write(f)

try:
	s = HTMLSession()

	# Get captive portal URL
	# It won't redirect, just replace the HTML contents
	first_redir = s.get('http://captive.apple.com/', allow_redirects=True)

	# Get actual portal URL
	captive_url = first_redir.headers.get('Location', None)

	# Retrieve captive portal HTML
	captive = s.get(captive_url, allow_redirects=True)

	# Get token, portal ID, and generate a payload.
	token = captive.html.find('input[name=token]', first=True).attrs.get('value')
	portal_id = captive.html.find('input[name=portal]', first=True).attrs.get('value')
	payload = {
		'user.username': config['auth'].get('username', False),
		'user.password': config['auth'].get('password', False),
		'token': token,
		'portal': portal_id
	}

	print("Signing in to captive portal...")

	# Login with the credentials & token
	result = s.post('https://ise.uprrp.edu:8443/portal/LoginSubmit.action?from=LOGIN', data=payload)

	# Get session ID to exec CoA
	session_id = captive.cookies.get_dict().get('portalSessionId')

	# Prepare CoA payload
	coa_payload = {
		'delayToCoA': 0,
		'coaType': 'REAUTH',
		'waitForCoA': True,
		'portalSessionId': session_id,
		'token': token,
	}

	print("Executing CoA...")

	do_coa = s.post('https://ise.uprrp.edu:8443/portal/DoCoA.action', data=coa_payload)

	check_coa = s.get('https://ise.uprrp.edu:8443/portal/CheckCoAStatus.action?_=%s' % int(time.time()))

	print("Checking CoA status...")

	if check_coa.status_code == 200:
		print("\033[92mYou are now logged in.\033[0m")
	else:
		print("\033[91mFailed to log in.\033[0m")
except Exception as e:
		print("\033[91mUh oh, something went wrong.\033[0m")
		print(e)
