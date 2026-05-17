#!/usr/bin/python3
"""CLI tool for Intel Wiki (Confluence)"""

import argparse
import json
import os
from pathlib import Path
import sys
import urllib3

import requests

# Disable SSL warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_confluence_pat():
    """Get PAT from environment or file."""
    pat = os.environ.get('CONFLUENCE_PAT')
    if pat:
        return pat

    # Try reading from ~/.intel_wiki_pat
    pat_file = Path.home() / '.intel_wiki_pat'
    if pat_file.exists():
        return pat_file.read_text().strip()

    return None


CONFLUENCE_PAT = get_confluence_pat()
CONFLUENCE_BASE_URL = os.environ.get('CONFLUENCE_BASE_URL', 'https://wiki.ith.intel.com/rest/api')


def get_session():
    """Create a requests session with auth headers."""
    if not CONFLUENCE_PAT:
        print("Error: CONFLUENCE_PAT environment variable or ~/.intel_wiki_pat file is required", file=sys.stderr)
        print("Get your PAT from: https://wiki.ith.intel.com/plugins/personalaccesstokens/usertokens.action", file=sys.stderr)
        sys.exit(1)

    session = requests.Session()
    session.headers.update({
        'Authorization': f'Bearer {CONFLUENCE_PAT}',
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    })
    session.verify = False
    # Bypass proxy for internal Intel sites
    session.proxies = {'http': None, 'https': None}
    session.trust_env = False
    return session


def search_pages(cql: str, limit: int = 10):
    """Search Confluence pages using CQL query."""
    session = get_session()
    resp = session.get(f'{CONFLUENCE_BASE_URL}/content', params={'cql': cql, 'limit': limit})
    resp.raise_for_status()
    return resp.json()


def search_content(query: str):
    """Search Confluence content by text."""
    session = get_session()
    cql = f'text~"{query}" OR title~"{query}"'
    resp = session.get(f'{CONFLUENCE_BASE_URL}/search', params={'cql': cql})
    resp.raise_for_status()
    return resp.json()


def get_page(page_id: str = None, title: str = None):
    """Get a Confluence page by ID or title."""
    session = get_session()
    if page_id:
        resp = session.get(f'{CONFLUENCE_BASE_URL}/content/{page_id}', params={'expand': 'body.storage'})
    elif title:
        resp = session.get(f'{CONFLUENCE_BASE_URL}/content', params={'title': title, 'expand': 'body.storage'})
    else:
        raise ValueError('Either page_id or title must be provided')
    resp.raise_for_status()
    return resp.json()


def get_current_version(page_id: str) -> int:
    """Get the current version number of a page."""
    session = get_session()
    resp = session.get(f'{CONFLUENCE_BASE_URL}/content/{page_id}')
    resp.raise_for_status()
    return resp.json()['version']['number']


def create_page(space: str, title: str, body: str, parent_id: str = None):
    """Create a new Confluence page."""
    session = get_session()
    data = {
        'type': 'page',
        'title': title,
        'space': {'key': space},
        'body': {
            'storage': {
                'value': body,
                'representation': 'storage',
            },
        },
    }
    if parent_id:
        data['ancestors'] = [{'id': parent_id}]
    resp = session.post(f'{CONFLUENCE_BASE_URL}/content', json=data)
    resp.raise_for_status()
    return resp.json()


def create_draft(space: str, title: str, body: str, parent_id: str = None):
    """Create a new Confluence draft page."""
    session = get_session()
    data = {
        'type': 'page',
        'title': title,
        'space': {'key': space},
        'body': {
            'storage': {
                'value': body,
                'representation': 'storage',
            },
        },
        'status': 'draft',
    }
    if parent_id:
        data['ancestors'] = [{'id': parent_id}]
    resp = session.post(f'{CONFLUENCE_BASE_URL}/content', json=data)
    resp.raise_for_status()
    return resp.json()


def update_page(page_id: str, title: str, body: str, space: str, parent_id: str = None):
    """Update an existing Confluence page."""
    session = get_session()
    version = get_current_version(page_id) + 1
    data = {
        'id': page_id,
        'type': 'page',
        'title': title,
        'body': {
            'storage': {
                'value': body,
                'representation': 'storage',
            },
        },
        'version': {'number': version},
        'space': {'key': space},
    }
    if parent_id:
        data['ancestors'] = [{'id': parent_id}]
    resp = session.put(f'{CONFLUENCE_BASE_URL}/content/{page_id}', json=data)
    resp.raise_for_status()
    return resp.json()


def move_page(page_id: str, title: str, space: str, new_parent_id: str):
    """Move a Confluence page to a new parent."""
    session = get_session()
    version = get_current_version(page_id) + 1
    data = {
        'id': page_id,
        'type': 'page',
        'title': title,
        'version': {'number': version},
        'space': {'key': space},
        'ancestors': [{'id': new_parent_id}],
    }
    resp = session.put(f'{CONFLUENCE_BASE_URL}/content/{page_id}', json=data)
    resp.raise_for_status()
    return resp.json()


def get_comments(page_id: str):
    """Get comments for a Confluence page."""
    session = get_session()
    resp = session.get(f'{CONFLUENCE_BASE_URL}/content/{page_id}/child/comment')
    resp.raise_for_status()
    return resp.json()


def add_comment(page_id: str, comment: str):
    """Add a comment to a Confluence page."""
    session = get_session()
    data = {
        'type': 'comment',
        'container': {'id': page_id, 'type': 'page'},
        'body': {
            'storage': {
                'value': comment,
                'representation': 'storage',
            },
        },
    }
    resp = session.post(f'{CONFLUENCE_BASE_URL}/content', json=data)
    resp.raise_for_status()
    return resp.json()


def get_child_pages(page_id: str):
    """Get child pages for a Confluence page."""
    session = get_session()
    resp = session.get(f'{CONFLUENCE_BASE_URL}/content/{page_id}/child/page')
    resp.raise_for_status()
    return resp.json()


def main():
    parser = argparse.ArgumentParser(description='CLI tool for Intel Wiki (Confluence)')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # search-pages
    sp_search_pages = subparsers.add_parser('search-pages', help='Search pages using CQL')
    sp_search_pages.add_argument('-q', '--cql', required=True, help='CQL query string')
    sp_search_pages.add_argument('-l', '--limit', type=int, default=10, help='Limit results')

    # search
    sp_search = subparsers.add_parser('search', help='Search content by text')
    sp_search.add_argument('query', help='Search query text')

    # get
    sp_get = subparsers.add_parser('get', help='Get a page by ID or title')
    sp_get.add_argument('-i', '--id', help='Page ID')
    sp_get.add_argument('-t', '--title', help='Page title')

    # create
    sp_create = subparsers.add_parser('create', help='Create a new page')
    sp_create.add_argument('-s', '--space', required=True, help='Space key')
    sp_create.add_argument('-t', '--title', required=True, help='Page title')
    sp_create.add_argument('-b', '--body', required=True, help='Page body (HTML/storage format)')
    sp_create.add_argument('-p', '--parent', help='Parent page ID')

    # create-draft
    sp_draft = subparsers.add_parser('create-draft', help='Create a draft page')
    sp_draft.add_argument('-s', '--space', required=True, help='Space key')
    sp_draft.add_argument('-t', '--title', required=True, help='Page title')
    sp_draft.add_argument('-b', '--body', required=True, help='Page body (HTML/storage format)')
    sp_draft.add_argument('-p', '--parent', help='Parent page ID')

    # update
    sp_update = subparsers.add_parser('update', help='Update an existing page')
    sp_update.add_argument('-i', '--id', required=True, help='Page ID')
    sp_update.add_argument('-t', '--title', required=True, help='Page title')
    sp_update.add_argument('-b', '--body', required=True, help='Page body (HTML/storage format)')
    sp_update.add_argument('-s', '--space', required=True, help='Space key')
    sp_update.add_argument('-p', '--parent', help='Parent page ID')

    # move
    sp_move = subparsers.add_parser('move', help='Move a page to a new parent')
    sp_move.add_argument('-i', '--id', required=True, help='Page ID')
    sp_move.add_argument('-t', '--title', required=True, help='Page title')
    sp_move.add_argument('-s', '--space', required=True, help='Space key')
    sp_move.add_argument('-p', '--parent', required=True, help='New parent page ID')

    # comments
    sp_comments = subparsers.add_parser('comments', help='Get comments for a page')
    sp_comments.add_argument('-i', '--id', required=True, help='Page ID')

    # add-comment
    sp_add_comment = subparsers.add_parser('add-comment', help='Add a comment to a page')
    sp_add_comment.add_argument('-i', '--id', required=True, help='Page ID')
    sp_add_comment.add_argument('-c', '--comment', required=True, help='Comment text')

    # children
    sp_children = subparsers.add_parser('children', help='Get child pages')
    sp_children.add_argument('-i', '--id', required=True, help='Page ID')

    # check-setup
    subparsers.add_parser('check-setup', help='Check if PAT is configured')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Handle check-setup before other commands
    if args.command == 'check-setup':
        pat_file = Path.home() / '.intel_wiki_pat'
        if CONFLUENCE_PAT:
            if os.environ.get('CONFLUENCE_PAT'):
                print("OK: PAT configured via CONFLUENCE_PAT environment variable")
            else:
                print(f"OK: PAT configured via {pat_file}")
            sys.exit(0)
        else:
            print("NOT CONFIGURED: PAT is not set up", file=sys.stderr)
            print("", file=sys.stderr)
            print("To set up your PAT:", file=sys.stderr)
            print("1. Visit: https://wiki.ith.intel.com/plugins/personalaccesstokens/usertokens.action", file=sys.stderr)
            print("2. Create a new token and copy it", file=sys.stderr)
            print("3. Save it:", file=sys.stderr)
            print(f'   echo "YOUR_TOKEN" > {pat_file}', file=sys.stderr)
            print(f'   chmod 600 {pat_file}', file=sys.stderr)
            sys.exit(1)

    try:
        if args.command == 'search-pages':
            result = search_pages(args.cql, args.limit)
        elif args.command == 'search':
            result = search_content(args.query)
        elif args.command == 'get':
            if not args.id and not args.title:
                print('Error: Either --id or --title is required', file=sys.stderr)
                sys.exit(1)
            result = get_page(args.id, args.title)
        elif args.command == 'create':
            result = create_page(args.space, args.title, args.body, args.parent)
        elif args.command == 'create-draft':
            result = create_draft(args.space, args.title, args.body, args.parent)
        elif args.command == 'update':
            result = update_page(args.id, args.title, args.body, args.space, args.parent)
        elif args.command == 'move':
            result = move_page(args.id, args.title, args.space, args.parent)
        elif args.command == 'comments':
            result = get_comments(args.id)
        elif args.command == 'add-comment':
            result = add_comment(args.id, args.comment)
        elif args.command == 'children':
            result = get_child_pages(args.id)
        else:
            parser.print_help()
            sys.exit(1)

        print(json.dumps(result, indent=2))

    except requests.HTTPError as e:
        print(f'HTTP Error: {e.response.status_code} - {e.response.text}', file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
