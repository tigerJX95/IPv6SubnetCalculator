# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Release-only attachment decisions; fixed-ID uploads never overwrite existing assets."""
import argparse
import ast
import json
import os
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]


def app_version():
    tree = ast.parse((ROOT/'app_info.py').read_text(encoding='utf-8'))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'APP_VERSION' for t in node.targets):
            value = ast.literal_eval(node.value)
            if isinstance(value, str) and re.fullmatch(r'\d+\.\d+(?:\.\d+)?', value):
                return value
    raise ValueError('Invalid APP_VERSION')


def api(*arguments):
    result = subprocess.run(['gh', *arguments], check=True, capture_output=True, text=True, encoding='utf-8', timeout=120)
    return json.loads(result.stdout)


def snapshot(repository, release_id, tag):
    if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+', repository) or type(release_id) is not int or release_id <= 0:
        raise ValueError('Invalid repository or Release ID')
    if not re.fullmatch(r'v\d+\.\d+(?:\.\d+)?', tag):
        raise ValueError('Invalid version tag')
    release = api('api', f'repos/{repository}/releases/{release_id}')
    if release.get('id') != release_id or release.get('tag_name') != tag or release.get('draft') is not False:
        raise ValueError('Release identity changed or is still a draft')
    pages = api('api', f'repos/{repository}/releases/{release_id}/assets?per_page=100', '--paginate', '--slurp')
    if not isinstance(pages, list) or any(not isinstance(page, list) for page in pages):
        raise ValueError('Invalid attachment pagination')
    assets = [asset for page in pages for asset in page]
    if any(not isinstance(a, dict) or not isinstance(a.get('name'), str) for a in assets):
        raise ValueError('Invalid attachment metadata')
    return release, assets


def build_decision(repository, release_id, tag):
    release, assets = snapshot(repository, release_id, tag)
    executables = [a for a in assets if a['name'].lower().endswith('.exe')]
    if executables:
        if any(a.get('state') != 'uploaded' or type(a.get('size')) is not int or a['size'] <= 0 for a in executables):
            raise ValueError('An EXE attachment is incomplete; finish or remove it before retrying')
        return False, 'EXE attachment already present; automatic build and upload skipped.'
    if release.get('immutable'):
        raise ValueError('Release is immutable and cannot accept an EXE attachment')
    return True, 'No EXE attachments; build and attach the verified single-file EXE.'


def publish(repository, release_id, tag, package):
    version = app_version()
    if tag != 'v'+version:
        raise ValueError('Release tag does not match APP_VERSION')
    package = Path(package).resolve()
    expected = f'IPv6SubnetCalculator_V{version}.exe'
    if package.name != expected or not package.is_file() or package.stat().st_size <= 0:
        raise ValueError('Missing, empty or incorrectly named EXE')
    size = package.stat().st_size
    build, reason = build_decision(repository, release_id, tag)
    if not build:
        return reason
    # Fixed Release ID; POST has no replacement behavior. A same-name race fails.
    asset = api('api', '--method', 'POST',
                f'https://uploads.github.com/repos/{repository}/releases/{release_id}/assets?name={quote(expected, safe="")}',
                '-H', 'Content-Type: application/octet-stream', '--input', str(package))
    if asset.get('name') != expected or asset.get('state') != 'uploaded' or asset.get('size') != size:
        raise ValueError('GitHub did not confirm the complete EXE upload')
    return 'Attached verified EXE: '+expected


def verify_main_history(tag):
    if tag != 'v'+app_version():
        raise ValueError('Release tag does not match APP_VERSION')

    def git(*arguments):
        return subprocess.run(['git', *arguments], cwd=ROOT, check=True, capture_output=True,
                              text=True, encoding='utf-8', timeout=180).stdout.strip()

    shallow = git('rev-parse', '--is-shallow-repository')
    if shallow not in ('true', 'false'):
        raise ValueError('Unknown Git history state')
    arguments = ['fetch', '--no-tags']
    if shallow == 'true':
        arguments.append('--unshallow')
    git(*arguments, 'origin', '+refs/heads/main:refs/remotes/origin/main')
    git('merge-base', '--is-ancestor', 'HEAD', 'refs/remotes/origin/main')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['inspect', 'publish', 'version', 'history'])
    parser.add_argument('--repository', default=os.environ.get('GITHUB_REPOSITORY', ''))
    parser.add_argument('--release-id', type=int, default=0)
    parser.add_argument('--tag', default='')
    parser.add_argument('--package', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'version':
            print(app_version())
            return 0
        if args.command == 'history':
            verify_main_history(args.tag)
            print('Release version and main history verified without fetching tags.')
            return 0
        if args.command == 'inspect':
            build, reason = build_decision(args.repository, args.release_id, args.tag)
            with Path(os.environ['GITHUB_OUTPUT']).open('a', encoding='utf-8') as output:
                output.write('build='+str(build).lower()+'\n')
        else:
            if args.package is None:
                raise ValueError('Package is required')
            reason = publish(args.repository, args.release_id, args.tag, args.package)
        print(reason)
        if os.environ.get('GITHUB_STEP_SUMMARY'):
            with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a', encoding='utf-8') as summary:
                summary.write(reason+'\n')
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
        # Do not print CLI request details or token-bearing subprocess output.
        print('Release attachment operation failed: '+type(exc).__name__)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
