Review: quiz_app.py vs SPEC.md
[PASS] Acceptance: App runs as a .py script without trivial import/runtime errors — Single entrypoint main() at 532:554:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py; dependencies declared in requirements.txt (cryptography).

[PASS] Acceptance: Users can log in or create an account — auth_flow() (320:364:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py) supports create (register) and login (verify_login); duplicate username is rejected with a retry (338:340:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py), matching the spec’s error-handling bullet.

[PASS] Acceptance: Questions load from JSON — load_questions() (225:238:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py) reads questions.json, validates a non-empty questions array, and handles parse/read errors with a message and sys.exit(1).

[PASS] Acceptance: Score history is relatively secure and not human-readable — SecureScoreStore (99:223:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py) stores per-user Fernet-encrypted payloads in score_history.sec; plaintext usernames in the file align with the spec’s note that usernames may be visible while passwords/scores are protected inside the ciphertext.

[PASS] Acceptance: Chosen difficulty determines which questions are asked — filter_by_difficulty() (241:247:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py) filters by difficulty; run_quiz() builds the pool from that before sampling (409:414:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py).

[WARN] Acceptance: Errors handled without crashing — JSON missing/invalid is handled (34:37:/Users/manyakhemka/Desktop/quiz-app/quiz_app_app.py — typo: file is quiz_app.py lines 225-237). Invalid menu/input is generally retried via prompt_choice / prompt_int_in_range. However, an empty question pool (e.g. difficulty filter matches no questions, or malformed items with type: multiple_choice and empty options) leads to max_q == 0 and prompt_int_in_range(..., 1, 0) (422:427:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py), which never accepts a valid number and loops forever — effectively a hang, not a clean error. Similar risk in ask_multiple_choice when n == 0 (371:381:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py).

[PASS] Spec: Welcome → login / create / quit; main menu with settings; quiz flow; feedback; summary; stats; loop or exit — Implemented in welcome_screen, auth_flow, main_menu, and run_quiz (310:529:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py). Optional 'back' during auth matches the idea of leaving auth without logging in (spec line 7 uses “quit”; behavior is close).

[PASS] Spec: Missing JSON → error and exit — 34:37:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py and 226:233:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py.

[PASS] Spec: Invalid input → reprompt — Centralized in prompt_choice (283:295:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py), prompt_int_in_range (297:307:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py), and per-question loops.

[PASS] Spec: Passwords not easily discoverable — PBKDF2-HMAC-SHA256 with 390,000 iterations (28:29:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py, 57:67:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py); salts and hashes stored inside encrypted payload.

[PASS] Spec: Like/dislike affects future questions — get_feedback_weights / weighted_pick_questions (200:272:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py, 474:479:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py).

[PASS] Spec: Difficulty-based scoring (+1 / +2 / +3) — DIFFICULTY_POINTS and run_quiz scoring (31:31:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py, 441:459:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py).

[FAIL] Logic / data integrity: Failed decrypt for an existing user can wipe stored data — If username exists in _lines but _decrypt_payload fails (corrupt line, tampered blob, or new .app_key after the old one was lost), get_payload() returns a default empty payload including empty password (173:184:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py). The next append_session or set_question_feedback calls _write_payload and replaces the stored blob, effectively destroying the prior ciphertext and locking the user out. For a “secure” store, decrypt failure for a known user should abort or require recovery, not silently rewrite.

[WARN] Security: Encryption key and data file permissions — .app_key is chmod 0o600 when possible (50:53:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py), but score_history.sec is written without tightening permissions (125:128:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py), so default umask may leave it group/world-readable on multi-user systems. Anyone who can read .app_key and score_history.sec can decrypt scores (expected limitation for local symmetric encryption).

[WARN] Security / UX: Passwords read from stdin — Passwords are plain input() (341:346:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py, 352:357:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py); typical CLI limitation (echo may show typing). Not a spec violation; worth noting for shared terminals.

[WARN] Robustness: EOF / piped input — prompt_line turns EOFError into "" (275:280:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py), so prompt_choice can loop forever printing “Invalid input” with no clean exit.

[WARN] Code quality: Duplicated “ensure data dir” — _ensure_data_dir() appears in both _load_or_create_fernet and _save; harmless but slightly redundant.

[PASS] Answers checked and correct answer shown after each question — 456:462:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py.

[WARN] Multiple-choice matching is case- and whitespace-sensitive — answers_match uses exact string equality for non–short-answer / non–true/false (89:96:/Users/manyakhemka/Desktop/quiz-app/quiz_app.py). That matches “pick option text” flow today; unusual JSON (e.g. answer not exactly equal to one option string) could mark correct answers wrong.

