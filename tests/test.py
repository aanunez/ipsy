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

#filecmp.cmp('diff_test', 'out/diff_test')
#os.system('ipsy diff rom1 patch1 -o diff_test')


#filecmp.cmp('file1.txt', 'file1.txt')


print("Done!")
