#!/usr/bin/env python3
import os, filecmp

os.chdir(os.sep.join(os.path.realpath(__file__).split(os.sep)[:-2]))
print("Running tests...")

os.system('python3 -m ../ipsy -o _output1 diff tests/diff_test/rom tests/diff_test/patched_rom')
if not filecmp.cmp('diff_test/output1', '_output1'):
    print('Issue on diff_test w/o rle')

os.system('python3 -m ../ipsy -o _output2 diff -rle tests/diff_test/rom tests/diff_test/patched_rom')
if not filecmp.cmp('diff_test/output2', '_output2'):
    print('Issue on diff_test w/ rle')

os.system('python3 -m ../ipsy -o _output3 patch tests/patch_test/rom tests/patch_test/patch')
if not filecmp.cmp('patch_test/output3', '_output3'):
    print('Issue on patch_test')

os.system('python3 -m ../ipsy -o _output4 merge tests/merge_test/patch1 tests/merge_test/patch2')
if not filecmp.cmp('merge_test/output4', '_output4'):
    print('Issue on merge_test')

print("Done!")
