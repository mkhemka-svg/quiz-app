#!/usr/bin/env python3
"""
Quiz application — main logic (see SPEC.md).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import random
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from cryptography.fernet import Fernet, InvalidToken

# --- Paths (project root = directory containing this file) ---
ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = ROOT / "questions.json"
DATA_DIR = ROOT / "data"
KEY_PATH = DATA_DIR / ".app_key"
SCORE_HISTORY_PATH = ROOT / "score_history.sec"

PBKDF2_ITERATIONS = 390000
SALT_BYTES = 16

DIFFICULTY_POINTS = {"easy": 1, "medium": 2, "difficult": 3}


def _die_json_missing() -> None:
    print("Error: questions file is missing. Expected:", QUESTIONS_PATH)
    sys.exit(1)


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_or_create_fernet() -> Fernet:
    _ensure_data_dir()
    if KEY_PATH.exists():
        key = KEY_PATH.read_bytes()
    else:
        key = Fernet.generate_key()
        KEY_PATH.write_bytes(key)
        try:
            os.chmod(KEY_PATH, 0o600)
        except OSError:
            pass
    return Fernet(key)


def _hash_password(password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
    if salt is None:
        salt = os.urandom(SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
        dklen=32,
    )
    return salt, dk


def _verify_password(password: str, salt_b64: str, hash_b64: str) -> bool:
    try:
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(hash_b64)
    except (ValueError, TypeError):
        return False
    _, dk = _hash_password(password, salt=salt)
    return hashlib.compare_digest(dk, expected)


def question_key(q: dict[str, Any]) -> str:
    raw = f"{q.get('question', '')}|{q.get('category', '')}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def normalize_short_answer(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def answers_match(expected: str, given: str, qtype: str) -> bool:
    exp = expected.strip()
    got = given.strip()
    if qtype == "short_answer":
        return normalize_short_answer(got) == normalize_short_answer(exp)
    if qtype == "true_false":
        return got.lower() == exp.lower()
    return got == exp


class SecureScoreStore:
    """
    score_history.sec: one line per user — username TAB base64(ciphertext).
    Usernames may be visible; password verification data and scores live inside ciphertext.
    """

    def __init__(self) -> None:
        self._fernet = _load_or_create_fernet()
        self._lines: dict[str, str] = {}
        self._load()

    def _load(self) -> None:
        if not SCORE_HISTORY_PATH.exists():
            return
        text = SCORE_HISTORY_PATH.read_text(encoding="utf-8", errors="replace")
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t", 1)
            if len(parts) != 2:
                continue
            user, blob = parts[0].strip(), parts[1].strip()
            if user:
                self._lines[user] = blob

    def _save(self) -> None:
        _ensure_data_dir()
        lines = [f"{u}\t{b}" for u, b in sorted(self._lines.items())]
        SCORE_HISTORY_PATH.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def user_exists(self, username: str) -> bool:
        return username in self._lines

    def register(self, username: str, password: str) -> None:
        if self.user_exists(username):
            raise ValueError("username taken")
        salt, dk = _hash_password(password)
        payload = {
            "password": {
                "salt_b64": base64.b64encode(salt).decode("ascii"),
                "hash_b64": base64.b64encode(dk).decode("ascii"),
            },
            "sessions": [],
            "question_feedback": {},
        }
        token = self._fernet.encrypt(json.dumps(payload).encode("utf-8"))
        self._lines[username] = base64.b64encode(token).decode("ascii")
        self._save()

    def verify_login(self, username: str, password: str) -> bool:
        if not self.user_exists(username):
            return False
        payload = self._decrypt_payload(username)
        if not payload:
            return False
        p = payload.get("password") or {}
        return _verify_password(password, p.get("salt_b64", ""), p.get("hash_b64", ""))

    def _decrypt_payload(self, username: str) -> dict[str, Any] | None:
        blob = self._lines.get(username)
        if not blob:
            return None
        try:
            raw = self._fernet.decrypt(base64.b64decode(blob.encode("ascii")))
            return json.loads(raw.decode("utf-8"))
        except (InvalidToken, ValueError, json.JSONDecodeError, TypeError):
            return None

    def _write_payload(self, username: str, payload: dict[str, Any]) -> None:
        token = self._fernet.encrypt(json.dumps(payload).encode("utf-8"))
        self._lines[username] = base64.b64encode(token).decode("ascii")
        self._save()

    def get_payload(self, username: str) -> dict[str, Any]:
        p = self._decrypt_payload(username)
        if p is None:
            return {
                "password": {},
                "sessions": [],
                "question_feedback": {},
            }
        p.setdefault("sessions", [])
        p.setdefault("question_feedback", {})
        p.setdefault("password", {})
        return p

    def append_session(
        self,
        username: str,
        session: dict[str, Any],
    ) -> None:
        payload = self.get_payload(username)
        payload["sessions"].append(session)
        self._write_payload(username, payload)

    def set_question_feedback(self, username: str, qkey: str, sentiment: str) -> None:
        payload = self.get_payload(username)
        payload["question_feedback"][qkey] = sentiment
        self._write_payload(username, payload)

    def get_feedback_weights(self, username: str) -> dict[str, float]:
        payload = self.get_payload(username)
        out: dict[str, float] = {}
        for k, v in (payload.get("question_feedback") or {}).items():
            if v == "like":
                out[k] = 1.65
            elif v == "dislike":
                out[k] = 0.22
        return out

    def weak_categories(self, username: str, top_n: int = 3) -> list[str]:
        """Extension: categories with most incorrect answers across past sessions."""
        payload = self.get_payload(username)
        wrong_by_cat: dict[str, int] = {}
        for s in payload.get("sessions") or []:
            for row in s.get("answers_detail") or []:
                if not row.get("correct"):
                    cat = row.get("category") or "Unknown"
                    wrong_by_cat[cat] = wrong_by_cat.get(cat, 0) + 1
        if not wrong_by_cat:
            return []
        ranked = sorted(wrong_by_cat.items(), key=lambda x: (-x[1], x[0]))
        return [c for c, _ in ranked[:top_n]]


def load_questions() -> list[dict[str, Any]]:
    if not QUESTIONS_PATH.is_file():
        _die_json_missing()
    try:
        with open(QUESTIONS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print("Error: could not read or parse questions file:", e)
        sys.exit(1)
    qs = data.get("questions")
    if not isinstance(qs, list) or not qs:
        print("Error: questions.json has no valid 'questions' array.")
        sys.exit(1)
    return qs


def filter_by_difficulty(
    questions: list[dict[str, Any]], choice: str
) -> list[dict[str, Any]]:
    choice = choice.strip().lower()
    if choice in ("all", "mixed", "any"):
        return list(questions)
    return [q for q in questions if str(q.get("difficulty", "")).lower() == choice]


def weighted_pick_questions(
    pool: list[dict[str, Any]],
    count: int,
    weights_map: dict[str, float],
) -> list[dict[str, Any]]:
    if count <= 0 or not pool:
        return []
    pool = list(pool)
    if count >= len(pool):
        random.shuffle(pool)
        return pool

    def weight_for(q: dict[str, Any]) -> float:
        w = weights_map.get(question_key(q), 1.0)
        return max(w, 0.05)

    picked: list[dict[str, Any]] = []
    work = list(pool)
    for _ in range(count):
        ws = [weight_for(q) for q in work]
        idx = random.choices(range(len(work)), weights=ws, k=1)[0]
        picked.append(work.pop(idx))
    return picked


def prompt_line(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        print()
        return ""


def prompt_choice(
    prompt: str,
    valid: set[str],
    *,
    case_insensitive: bool = True,
) -> str:
    while True:
        raw = prompt_line(prompt)
        check = raw.lower() if case_insensitive else raw
        if check in valid:
            return check
        print("Invalid input. Please enter one of:", ", ".join(sorted(valid)))


def prompt_int_in_range(prompt: str, low: int, high: int) -> int:
    while True:
        raw = prompt_line(prompt)
        try:
            n = int(raw)
        except ValueError:
            print(f"Invalid input. Enter a whole number between {low} and {high}.")
            continue
        if low <= n <= high:
            return n
        print(f"Invalid input. Enter a number between {low} and {high}.")


def welcome_screen() -> str:
    print("\n" + "=" * 50)
    print("  Welcome to the Quiz App")
    print("=" * 50)
    print("  1) Log in")
    print("  2) Create an account")
    print("  3) Quit")
    return prompt_choice("Choose an option (1/2/3): ", {"1", "2", "3"})


def auth_flow(store: SecureScoreStore) -> str | None:
    """
    Returns username if logged in.
    None: user chose Quit on the welcome screen (exit app).
    During login or sign-up, type 'back' to return to the welcome screen without logging in.
    """
    while True:
        choice = welcome_screen()
        if choice == "3":
            return None
        if choice == "2":
            while True:
                user = prompt_line("Choose a username (or 'back' for welcome screen): ")
                if user.lower() == "back":
                    break
                if not user:
                    print("Username cannot be empty.")
                    continue
                if store.user_exists(user):
                    print("That username already exists. Please choose a different username.")
                    continue
                pw = prompt_line("Choose a password (or 'back' for welcome screen): ")
                if pw.lower() == "back":
                    break
                if not pw:
                    print("Password cannot be empty.")
                    continue
                store.register(user, pw)
                print("Account created. You are now logged in.")
                return user
        if choice == "1":
            while True:
                user = prompt_line("Username (or 'back' for welcome screen): ")
                if user.lower() == "back":
                    break
                pw = prompt_line("Password (or 'back' for welcome screen): ")
                if pw.lower() == "back":
                    break
                if store.verify_login(user, pw):
                    print("Login successful.")
                    return user
                print(
                    "Invalid username or password. Try again, type 'back' for the welcome screen, "
                    "or create an account."
                )


def ask_multiple_choice(q: dict[str, Any]) -> str:
    options = q.get("options") or []
    for i, opt in enumerate(options, start=1):
        print(f"  {i}) {opt}")
    n = len(options)
    while True:
        raw = prompt_line(f"Your answer (1-{n}): ")
        try:
            idx = int(raw)
        except ValueError:
            print(f"Invalid input. Enter a number from 1 to {n}.")
            continue
        if 1 <= idx <= n:
            return str(options[idx - 1])
        print(f"Invalid input. Enter a number from 1 to {n}.")


def ask_true_false(q: dict[str, Any]) -> str:
    print("  1) True")
    print("  2) False")
    while True:
        raw = prompt_line("Your answer (1=True, 2=False): ")
        if raw == "1":
            return "true"
        if raw == "2":
            return "false"
        print("Invalid input. Enter 1 for True or 2 for False.")


def ask_short_answer(q: dict[str, Any]) -> str:
    return prompt_line("Your answer: ")


def run_quiz(
    username: str,
    store: SecureScoreStore,
    all_questions: list[dict[str, Any]],
    *,
    practice_categories: list[str] | None = None,
) -> None:
    print("\n--- Quiz settings ---")
    print("Difficulty: easy (+1), medium (+2), difficult (+3) per correct answer.")
    diff = prompt_choice(
        "Difficulty filter (easy / medium / difficult / all): ",
        {"easy", "medium", "difficult", "all"},
    )
    pool = filter_by_difficulty(all_questions, diff if diff != "all" else "all")
    if practice_categories:
        pool = [q for q in pool if (q.get("category") or "") in practice_categories]
        if not pool:
            print(
                "No questions match practice mode for your weak categories at this difficulty."
            )
            print("Try 'all' difficulty or complete more quizzes to build a history.")
            return
    max_q = len(pool)
    n = prompt_int_in_range(
        f"How many questions? (1-{max_q}): ",
        1,
        max_q,
    )
    weights = store.get_feedback_weights(username)
    selected = weighted_pick_questions(pool, n, weights)
    if practice_categories:
        print(
            f"\n[Extension: Practice mode — focusing categories: {', '.join(practice_categories)}]\n"
        )

    score = 0
    max_points = 0
    answers_detail: list[dict[str, Any]] = []

    for i, q in enumerate(selected, start=1):
        qtype = str(q.get("type", "multiple_choice")).lower()
        diff_label = str(q.get("difficulty", "easy")).lower()
        pts = DIFFICULTY_POINTS.get(diff_label, 1)
        max_points += pts

        print(f"\n--- Question {i}/{len(selected)} ({diff_label}, up to {pts} pts) ---")
        print(q.get("question", ""))

        if qtype == "true_false":
            given = ask_true_false(q)
        elif qtype == "short_answer":
            given = ask_short_answer(q)
        else:
            given = ask_multiple_choice(q)

        correct_ans = str(q.get("answer", ""))
        ok = answers_match(correct_ans, given, qtype)
        if ok:
            score += pts
            print("Correct!")
        else:
            print("Incorrect.")
        print(f"The correct answer: {correct_ans}")

        answers_detail.append(
            {
                "question_key": question_key(q),
                "category": q.get("category"),
                "difficulty": diff_label,
                "correct": ok,
                "points_earned": pts if ok else 0,
            }
        )

        fb = prompt_choice(
            "Feedback: did you like this question? (like / dislike / skip): ",
            {"like", "dislike", "skip"},
        )
        if fb != "skip":
            store.set_question_feedback(username, question_key(q), fb)

    print("\n" + "=" * 50)
    print("  Final score summary")
    print("=" * 50)
    print(f"  Points earned: {score} / {max_points}")
    pct = (100.0 * score / max_points) if max_points else 0.0
    print(f"  Percentage: {pct:.1f}%")
    print("=" * 50)

    session = {
        "ended_at": datetime.now(timezone.utc).isoformat(),
        "score": score,
        "max_points": max_points,
        "question_count": len(selected),
        "difficulty_filter": diff,
        "practice_mode": bool(practice_categories),
        "answers_detail": answers_detail,
    }
    store.append_session(username, session)
    print("Your stats have been saved securely.")


def main_menu(
    username: str,
    store: SecureScoreStore,
    all_questions: list[dict[str, Any]],
) -> str:
    """Returns 'logout' or 'exit_app'."""
    while True:
        print("\n--- Main menu ---")
        print("  1) Take a quiz")
        print("  2) Extension: Practice weak areas (uses your past mistakes)")
        print("  3) Log out (back to welcome)")
        print("  4) Exit app")
        c = prompt_choice("Choose (1/2/3/4): ", {"1", "2", "3", "4"})
        if c == "1":
            run_quiz(username, store, all_questions, practice_categories=None)
        elif c == "2":
            weak = store.weak_categories(username, top_n=3)
            if not weak:
                print(
                    "No mistake history yet. Take a quiz first; then practice mode can target weak topics."
                )
            else:
                print(f"Weak areas detected: {', '.join(weak)}")
                run_quiz(username, store, all_questions, practice_categories=weak)
        elif c == "3":
            return "logout"
        else:
            return "exit_app"


def main() -> None:
    all_questions = load_questions()
    store = SecureScoreStore()

    print("\nQuiz data loaded.")

    while True:
        user = auth_flow(store)
        if user is None:
            print("Goodbye!")
            return

        while True:
            action = main_menu(user, store, all_questions)
            if action == "exit_app":
                print("Goodbye!")
                return
            if action == "logout":
                break


if __name__ == "__main__":
    main()
