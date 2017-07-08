#!/usr/bin/env python3

import os
import sys
import filecmp
import shutil

if os.path.join(*os.getcwd().split(os.sep)[-2:]) != 'ipsy/tests':
    print('Please run from test directory')
    sys.exit()

print("Running tests...")

os.system('ipsy -o _output1 diff diff_test/rom diff_test/patched_rom')
if not filecmp.cmp('diff_test/output1', '_output1'):
    print('Issue on diff_test w/o rle')

os.system('ipsy -o _output2 diff -rle diff_test/rom diff_test/patched_rom')
if not filecmp.cmp('diff_test/output2', '_output2'):
    print('Issue on diff_test w/o rle')

os.system('ipsy -o _output3 patch patch_test/rom patch_test/patch')
if not filecmp.cmp('patch_test/output3', '_output3'):
    print('Issue on patch_test')

os.system('ipsy -o _output4 merge merge_test/patch1 merge_test/patch2')
if not filecmp.cmp('merge_test/output4', '_output4'):
    print('Issue on merge_test')

print("Done!")
