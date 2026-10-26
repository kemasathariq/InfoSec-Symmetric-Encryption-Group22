# Merge and push guide (for Kema)

Goal: put the security work and Rifai's frontend on `main`, with a clean history, and hand over to Brilian.
Run every command inside the repo folder: `cd InfoSec-Symmetric-Encryption-Group22`.

## Before you start

    git status                       # should say: On branch security-crypto
    git config user.name             # must be your real name
    git config user.email            # must be the email linked to your GitHub account
    pip install -r requirements.txt  # needed to run the tests

Commit history is graded, so your commits must show your own name.

## 1. Commit your work (4 commits)

    git add BE/ciphers.py tests/test_ciphers.py requirements.txt
    git commit -m "Add AES-GCM, DES-CTR and RC4 encryption with tests"

    git add BE/Hooks.py BE/App.py tests/test_app_e2e.py
    git commit -m "Choose cipher per data type in hooks"

    git add bench
    git commit -m "Add benchmark and mode comparison"

    git add docs README.md .gitignore .env.example
    git commit -m "Add data classification, crypto design, report draft and handoff docs"

Check: `git status` should show nothing left, and `git log --oneline` should show 4 new commits.

## 2. Bring in Rifai's frontend

    git fetch origin
    git merge origin/rifa

Git will stop with 2 conflicts. This is expected.

**Conflict 1: `BE/App.py`** (the import lines)
Open the file and find the lines between `<<<<<<<` and `>>>>>>>`. The result must be exactly these three lines, with no markers:

    import ciphers
    import DB as db
    import Hooks as hooks

**Conflict 2: `README.md`** (the title line)
Keep the line `# Mobile Banking dengan Perlindungan Data Simetris (AES / DES / RC4)` and delete the other title and all markers.

Then:

    git add BE/App.py README.md
    git rm --cached BE/mbanking.db      # Rifai committed a database. It must not stay in git
    git commit -m "Merge frontend branch"

Check that no database is tracked: `git ls-files | grep -i "\.db"` must print nothing.
Check that no markers are left: `grep -rn "<<<<<<<\|>>>>>>>" BE README.md` must print nothing.

## 3. Test before pushing

    python -m unittest discover -s tests        # expect: Ran 12 tests ... OK

Then run the app by hand:

    export MASTER_KEY=$(python -c "import secrets;print(secrets.token_hex(32))")
    export LOOKUP_KEY=$(python -c "import secrets;print(secrets.token_hex(32))")
    cd BE && python App.py

Open http://127.0.0.1:5000. Register with a real image, a PDF and a short video, then log in and download each file. They must open normally. (The automated tests cover the API, but nobody has clicked through Rifai's page yet.)

## 4. Push and open the pull request

    git push -u origin security-crypto

On GitHub, open a pull request from `security-crypto` into `main`. Merge it with **"Create a merge commit"**. Do not use "Squash and merge", because that turns your commits into one and hides the history that is graded.

## 5. Tell the team

- **Rifai:** run `git checkout rifa && git merge main` before doing more work, so his branch has the new code.
- **Brilian:** run `git checkout main && git pull`, then follow `docs/HANDOFF_BRILIAN.md` from the top.

## If something goes wrong

- Merge got messy: `git merge --abort` puts everything back as before the merge.
- Tests fail after the merge: do not push. Send me the output.
- Pushed the wrong thing to a branch: tell the team before changing history. Do not use `--force` on `main`.
