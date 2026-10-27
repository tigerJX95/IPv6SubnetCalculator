# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 IPv6SubnetCalculator contributors
"""Release attachment policy, pagination and non-overwriting upload boundaries."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from tools import release_assets as r

REPO='owner/project'
TAG='v'+r.app_version()
RELEASE={'id':42,'tag_name':TAG,'draft':False}


def exe(name='custom.EXE',state='uploaded',size=12):
    return dict(name=name,state=state,size=size)


class ReleaseAssetTests(unittest.TestCase):
    def decision(self,assets,**changes):
        with patch.object(r,'snapshot',return_value=({**RELEASE,**changes},assets)):
            return r.build_decision(REPO,42,TAG)[0]

    def test_no_exe_builds_despite_automatic_source_archives_or_other_files(self):
        self.assertTrue(self.decision([]))
        self.assertTrue(self.decision([exe('source.zip'),exe('notes.txt'),exe('old.exe.zip')]))

    def test_any_complete_exe_skips_regardless_name_case_and_immutable(self):
        self.assertFalse(self.decision([exe()]))
        self.assertFalse(self.decision([exe('another.exe')],immutable=True))

    def test_incomplete_exe_fails_instead_of_skipping_or_overwriting(self):
        for asset in [exe(size=0),exe(size=-1),exe(size=True),exe(state='starter')]:
            with self.subTest(asset=asset),self.assertRaises(ValueError):self.decision([asset])

    def test_immutable_without_exe_fails(self):
        with self.assertRaises(ValueError):self.decision([],immutable=True)

    def test_pagination_finds_exe_on_later_page(self):
        pages=[[exe('notes'+str(i)+'.txt') for i in range(100)],[exe()]]
        with patch.object(r,'api',side_effect=[RELEASE,pages]) as api:
            self.assertFalse(r.build_decision(REPO,42,TAG)[0])
        self.assertEqual(api.call_args.args[-2:],('--paginate','--slurp'))

    def test_changed_identity_draft_invalid_inputs_and_malformed_pages_fail(self):
        for release in [{**RELEASE,'id':43},{**RELEASE,'tag_name':'v0.0'},{**RELEASE,'draft':True}]:
            with patch.object(r,'api',return_value=release),self.assertRaises(ValueError):r.snapshot(REPO,42,TAG)
        for repo,ident,tag in [('owner/project;evil',42,TAG),(REPO,0,TAG),(REPO,42,'v1.16;echo x')]:
            with patch.object(r,'api') as api,self.assertRaises(ValueError):
                r.snapshot(repo,ident,tag)
            api.assert_not_called()
        for pages in ({},[{}],[[{}]]):
            with patch.object(r,'api',side_effect=[RELEASE,pages]),self.assertRaises(ValueError):r.snapshot(REPO,42,TAG)

    def test_api_error_and_invalid_json_fail_closed(self):
        with patch.object(r.subprocess,'run',side_effect=subprocess.CalledProcessError(1,['gh'])),self.assertRaises(subprocess.CalledProcessError):r.api('api','endpoint')
        with patch.object(r.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'invalid','')),self.assertRaises(json.JSONDecodeError):r.api('api','endpoint')

    def package(self,directory):
        path=Path(directory)/f'IPv6SubnetCalculator_V{r.app_version()}.exe';path.write_bytes(b'MZtest');return path

    def test_publish_rechecks_and_keeps_manual_exe_appearing_during_build(self):
        with tempfile.TemporaryDirectory() as directory:
            path=self.package(directory)
            with patch.object(r,'snapshot',return_value=(RELEASE,[exe()])),patch.object(r,'api') as api:
                self.assertIn('skipped',r.publish(REPO,42,TAG,path))
                api.assert_not_called()

    def test_fixed_release_id_post_only_and_validated_confirmation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=self.package(directory)
            with patch.object(r,'snapshot',return_value=(RELEASE,[])),patch.object(r,'api',return_value=exe(path.name,size=path.stat().st_size)) as api:
                self.assertIn('Attached',r.publish(REPO,42,TAG,path))
            args=api.call_args.args
            self.assertEqual(args[:3],('api','--method','POST'))
            self.assertIn('/releases/42/assets?name=',args[3]);self.assertNotIn('--clobber',args)
            for reply in [exe(path.name,size=1),exe('different.exe'),exe(path.name,state='starter')]:
                with patch.object(r,'snapshot',return_value=(RELEASE,[])),patch.object(r,'api',return_value=reply),self.assertRaises(ValueError):r.publish(REPO,42,TAG,path)

    def test_publish_wrong_version_empty_or_missing_output_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path=self.package(directory)
            with self.assertRaises(ValueError):r.publish(REPO,42,'v0.0',path)
            path.write_bytes(b'')
            with self.assertRaises(ValueError):r.publish(REPO,42,TAG,path)
            path.unlink()
            with self.assertRaises(ValueError):r.publish(REPO,42,TAG,path)

    def test_cli_failure_does_not_write_success_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'output'
            with patch.dict('os.environ',{'GITHUB_OUTPUT':str(output)}),patch('sys.argv',['release_assets','inspect','--repository',REPO,'--release-id','42','--tag',TAG]),patch.object(r,'build_decision',side_effect=ValueError('invalid')):
                self.assertEqual(r.main(),1)
            self.assertFalse(output.exists())

    def test_workflow_release_only_trigger_manual_no_publish_and_raw_exe(self):
        import yaml
        workflow=yaml.load((r.ROOT/'.github/workflows/build.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(set(workflow['on']),{'release','workflow_dispatch'})
        self.assertEqual(workflow['on']['release']['types'],['published'])
        self.assertEqual(workflow['permissions'],{'contents':'read'})
        build=workflow['jobs']['build']
        self.assertEqual(build['if'],"needs.inspect.outputs.build == 'true'")
        steps=build['steps']
        attach=next(s for s in steps if 'release_assets.py publish' in s.get('run',''))
        self.assertEqual(attach['if'],"github.event_name == 'release'")
        artifact=next(s for s in steps if s.get('with',{}).get('archive')=='false')
        self.assertIn('steps.output.outputs.filename',artifact['with']['path'])
        verify=next(i for i,s in enumerate(steps) if 'tools/verify.py' in s.get('run',''))
        upload=steps.index(artifact);self.assertLess(verify,upload)
        self.assertTrue(any('release_assets.py history' in s.get('run','') for s in steps))


class ReleaseHistoryTests(unittest.TestCase):
    def test_shallow_fetches_only_main_without_tags_before_ancestry_check(self):
        def run(command,**kwargs):
            value='true' if 'rev-parse' in command else ''
            return subprocess.CompletedProcess(command,0,value,'')
        with patch.object(r.subprocess,'run',side_effect=run) as invoke:
            r.verify_main_history(TAG)
        commands=[c.args[0] for c in invoke.call_args_list]
        self.assertEqual(commands[1],['git','fetch','--no-tags','--unshallow','origin','+refs/heads/main:refs/remotes/origin/main'])
        self.assertEqual(commands[2],['git','merge-base','--is-ancestor','HEAD','refs/remotes/origin/main'])

    def test_complete_history_does_not_use_unshallow(self):
        with patch.object(r.subprocess,'run',side_effect=[subprocess.CompletedProcess([],0,'false',''),subprocess.CompletedProcess([],0,'',''),subprocess.CompletedProcess([],0,'','')]) as invoke:
            r.verify_main_history(TAG)
        self.assertNotIn('--unshallow',invoke.call_args_list[1].args[0])

    def test_wrong_tag_invalid_history_and_nonancestor_fail_closed(self):
        with patch.object(r.subprocess,'run') as invoke,self.assertRaises(ValueError):r.verify_main_history('v0.0')
        invoke.assert_not_called()
        with patch.object(r.subprocess,'run',return_value=subprocess.CompletedProcess([],0,'unknown','')),self.assertRaises(ValueError):r.verify_main_history(TAG)
        with patch.object(r.subprocess,'run',side_effect=[subprocess.CompletedProcess([],0,'true',''),subprocess.CompletedProcess([],0,'',''),subprocess.CalledProcessError(1,['git'])]),self.assertRaises(subprocess.CalledProcessError):r.verify_main_history(TAG)

    def test_real_shallow_clone_with_case_variant_tags_keeps_remote_tags(self):
        import os
        def git(root,*args):
            return subprocess.run(['git',*args],cwd=root,check=True,capture_output=True,text=True,env={**os.environ,'GIT_CONFIG_NOSYSTEM':'1'}).stdout.strip()
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);origin=root/'origin';origin.mkdir()
            git(origin,'init','-b','main');git(origin,'config','user.email','tests@example.invalid');git(origin,'config','user.name','Tests')
            (origin/'file').write_text('a');git(origin,'add','.');git(origin,'commit','-m','first')
            # Case-sensitive remote refs are created in a bare repo after cloning, for Windows compatibility.
            (origin/'file').write_text('b');git(origin,'commit','-am','second')
            remote=root/'remote.git';git(root,'clone','--bare',str(origin),str(remote))
            commit=git(remote,'rev-parse','HEAD')
            # packed-refs supports the colliding historic names even on Windows.
            with (remote/'packed-refs').open('ab') as refs:
                refs.write((commit+' refs/tags/V1.0\n'+commit+' refs/tags/v1.0\n').encode('ascii'))
            clone=root/'clone';git(root,'clone','--depth=1','--no-tags',remote.as_uri(),str(clone))
            self.assertEqual(git(clone,'rev-parse','--is-shallow-repository'),'true')
            with patch.object(r,'ROOT',clone),patch.object(r,'app_version',return_value=TAG[1:]):r.verify_main_history(TAG)
            self.assertEqual(git(clone,'rev-parse','--is-shallow-repository'),'false')
            self.assertEqual(git(clone,'tag','--list'),'')
            names=git(remote,'for-each-ref','--format=%(refname)','refs/tags')
            self.assertIn('refs/tags/V1.0',names);self.assertIn('refs/tags/v1.0',names)
