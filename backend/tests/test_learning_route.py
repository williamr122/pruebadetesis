import pytest
from backend.services.learning_route_service import get_route, update_unit_step, grade_quiz, _normalize_route


def test_new_student_route_initialization(client):
    """
    Test that a new student starts with:
    - Overall/general progress = 0%
    - Unit 1 is active, units 2, 3, 4 are locked
    - Individual unit progress = 0%
    """
    # Simply getting the route of a new user should default it correctly
    username = "pedrito"
    route = get_route(username)

    assert route["currentUnit"] == 1
    assert route["units"]["1"]["status"] == "active"
    assert route["units"]["1"]["progress"] == 0
    
    for i in range(2, 5):
        assert route["units"][str(i)]["status"] == "locked"
        assert route["units"][str(i)]["progress"] == 0


def test_sequential_step_progress_increment(client):
    """
    Test that progress increases strictly sequentially:
    - content_done: 20%
    - presentation_done: 40%
    - workshop_done: 60%
    - lesson_done: 80%
    """
    username = "pedrito"
    
    # Step 1: Content
    res = update_unit_step(username, unit_id=1, step="content", completed=True)
    route = res["route"]
    assert route["units"]["1"]["progress"] == 20
    assert route["units"]["1"]["status"] == "active"
    
    # Step 2: Presentation
    res = update_unit_step(username, unit_id=1, step="presentation", completed=True)
    route = res["route"]
    assert route["units"]["1"]["progress"] == 40
    
    # Step 3: Workshop
    res = update_unit_step(username, unit_id=1, step="workshop", completed=True)
    route = res["route"]
    assert route["units"]["1"]["progress"] == 60
    
    # Step 4: Lesson
    res = update_unit_step(username, unit_id=1, step="lesson", completed=True)
    route = res["route"]
    assert route["units"]["1"]["progress"] == 80


def test_sequential_locking_and_normalization(client):
    """
    Test that progress cannot skip steps (normalization caps progress if prerequisites are missing).
    """
    # If a unit has presentation_done = True but content_done = False, progress should be 0.
    bad_data = {
        "currentUnit": 1,
        "units": {
            "1": {
                "status": "active",
                "content_done": False,
                "presentation_done": True,
                "workshop_done": True,
                "lesson_done": True
            },
            "2": {"status": "locked"},
            "3": {"status": "locked"},
            "4": {"status": "locked"}
        }
    }
    normalized = _normalize_route(bad_data)
    assert normalized["units"]["1"]["progress"] == 0
    assert normalized["units"]["1"]["status"] == "active"


def test_quiz_grading_unlocks_next_unit_on_pass(client, monkeypatch):
    """
    Test that passing a unit quiz (>= 70%):
    - Sets current unit progress to 100%
    - Sets current unit status to "done"
    - Unlocks next unit (sets it to "active", with progress starting at 0%)
    - Updates currentUnit pointer
    """
    username = "pedrito"
    
    # Complete all prerequisites for unit 1
    update_unit_step(username, 1, "content", True)
    update_unit_step(username, 1, "presentation", True)
    update_unit_step(username, 1, "workshop", True)
    update_unit_step(username, 1, "lesson", True)
    
    # Mock QUIZ_BANK answers to pass
    from backend.services import learning_route_service
    quiz_questions = learning_route_service.QUIZ_BANK[1]
    answers = {q["id"]: q["answer"] for q in quiz_questions}
    
    res = grade_quiz(username, 1, answers)
    assert res["result"]["passed"] is True
    assert res["result"]["percent"] == 100
    
    route = res["route"]
    assert route["units"]["1"]["status"] == "done"
    assert route["units"]["1"]["progress"] == 100
    
    # Unit 2 should now be unlocked (active, with 0% progress)
    assert route["units"]["2"]["status"] == "active"
    assert route["units"]["2"]["progress"] == 0
    assert route["currentUnit"] == 2


def test_quiz_grading_stays_at_80_on_fail(client):
    """
    Test that failing a unit quiz (< 70%):
    - Keeps unit progress at 80%
    - Keeps unit status as "active"
    - Next unit remains locked
    """
    username = "pedrito"
    
    # Complete all prerequisites for unit 1
    update_unit_step(username, 1, "content", True)
    update_unit_step(username, 1, "presentation", True)
    update_unit_step(username, 1, "workshop", True)
    update_unit_step(username, 1, "lesson", True)
    
    # Submit incorrect answers to fail
    answers = {"u1-01": -1, "u1-02": -1, "u1-03": -1, "u1-04": -1, "u1-05": -1}
    
    res = grade_quiz(username, 1, answers)
    assert res["result"]["passed"] is False
    
    route = res["route"]
    assert route["units"]["1"]["status"] == "active"
    assert route["units"]["1"]["progress"] == 80
    assert route["units"]["2"]["status"] == "locked"
    assert route["currentUnit"] == 1
