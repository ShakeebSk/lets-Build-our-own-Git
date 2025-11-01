@echo off
echo ============================================== > pygit_test_log.txt
echo        🧪 PyGit Automated Test Script          >> pygit_test_log.txt
echo ============================================== >> pygit_test_log.txt
echo. >> pygit_test_log.txt

echo [STEP 1] Initialize Repository
python git.py init >> pygit_test_log.txt

echo [STEP 2] Add & Commit Initial Files
echo "Hello Git" > hello.txt
python git.py add hello.txt >> pygit_test_log.txt
python git.py commit -m "Initial commit" >> pygit_test_log.txt

echo [STEP 3] Branch Creation and Checkout
python git.py branch feature1 >> pygit_test_log.txt
python git.py checkout feature1 >> pygit_test_log.txt
echo "Feature code" > feature.py
python git.py add feature.py >> pygit_test_log.txt
python git.py commit -m "Add feature code" >> pygit_test_log.txt
python git.py checkout master >> pygit_test_log.txt

echo [STEP 4] Merge Branch
python git.py merge feature1 >> pygit_test_log.txt

echo [STEP 5] Cherry-pick
python git.py branch newbranch2 >> pygit_test_log.txt
python git.py checkout newbranch2 >> pygit_test_log.txt
echo "Login feature" > login.py
python git.py add login.py >> pygit_test_log.txt
python git.py commit -m "Added login.py" >> pygit_test_log.txt
python git.py checkout master >> pygit_test_log.txt
for /f "tokens=2" %%a in ('python git.py log ^| findstr /R "^commit" ^| head -n 1') do set commit=%%a
python git.py cherry-pick %commit% >> pygit_test_log.txt

echo [STEP 6] Tagging
python git.py tag v1.0 >> pygit_test_log.txt
python git.py tag -a v1.1 -m "Release version 1.1" >> pygit_test_log.txt
python git.py tag >> pygit_test_log.txt

echo [STEP 7] Stash
echo "Temporary change" > temp.txt
python git.py stash save "WIP: temporary test" >> pygit_test_log.txt
python git.py stash list >> pygit_test_log.txt
python git.py stash pop >> pygit_test_log.txt

echo [STEP 8] Reset
python git.py log >> pygit_test_log.txt
python git.py reset HEAD~1 --soft >> pygit_test_log.txt
python git.py reset HEAD~1 --mixed >> pygit_test_log.txt
python git.py reset HEAD~1 --hard >> pygit_test_log.txt

echo [STEP 9] Diff & Status
echo "Edit for diff" >> hello.txt
python git.py diff >> pygit_test_log.txt
python git.py add hello.txt >> pygit_test_log.txt
python git.py diff --cached >> pygit_test_log.txt
python git.py status >> pygit_test_log.txt

echo [STEP 10] Branch Deletion
python git.py branch -d newbranch2 >> pygit_test_log.txt

echo [STEP 11] Garbage Collection (if available)
python git.py gc >> pygit_test_log.txt

echo [STEP 12] Final Summary
python git.py log -n 5 >> pygit_test_log.txt
python git.py branch >> pygit_test_log.txt
python git.py tag >> pygit_test_log.txt
python git.py status >> pygit_test_log.txt

echo ============================================== >> pygit_test_log.txt
echo Tests Completed. Check pygit_test_log.txt for details. >> pygit_test_log.txt
echo ============================================== >> pygit_test_log.txt

echo ✅ PyGit test completed! Check pygit_test_log.txt for detailed output.
pause
