"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path to import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities_success(self):
        """Test that we can successfully fetch all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_activity_structure(self):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)


class TestSignup:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
    
    def test_signup_duplicate_fails(self):
        """Test that signing up twice for the same activity fails"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Chess%20Club/signup?email={email}"
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"]
    
    def test_signup_nonexistent_activity(self):
        """Test signup for a non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_signup_adds_to_participants(self):
        """Test that signup actually adds the participant to the activity"""
        email = "add-test@mergington.edu"
        
        # Get initial participant count
        initial = client.get("/activities").json()
        initial_count = len(initial["Basketball Team"]["participants"])
        
        # Signup
        response = client.post(
            f"/activities/Basketball%20Team/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Verify participant was added
        updated = client.get("/activities").json()
        updated_count = len(updated["Basketball Team"]["participants"])
        assert updated_count == initial_count + 1
        assert email in updated["Basketball Team"]["participants"]


class TestUnregister:
    """Test the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self):
        """Test successful unregister from an activity"""
        email = "unreg-test@mergington.edu"
        
        # First signup
        client.post(f"/activities/Tennis%20Club/signup?email={email}")
        
        # Then unregister
        response = client.post(
            f"/activities/Tennis%20Club/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
    
    def test_unregister_not_signed_up_fails(self):
        """Test that unregistering a non-signed-up participant fails"""
        response = client.post(
            "/activities/Drama%20Club/unregister?email=notaparticipant@test.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_nonexistent_activity(self):
        """Test unregister from a non-existent activity"""
        response = client.post(
            "/activities/Fake%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        email = "remove-test@mergington.edu"
        
        # Signup
        client.post(f"/activities/Art%20Studio/signup?email={email}")
        
        # Verify participant was added
        before = client.get("/activities").json()
        assert email in before["Art Studio"]["participants"]
        count_before = len(before["Art Studio"]["participants"])
        
        # Unregister
        client.post(f"/activities/Art%20Studio/unregister?email={email}")
        
        # Verify participant was removed
        after = client.get("/activities").json()
        assert email not in after["Art Studio"]["participants"]
        count_after = len(after["Art Studio"]["participants"])
        assert count_after == count_before - 1


class TestRootRedirect:
    """Test the root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that the root path redirects to the static index"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_unregister_cycle(self):
        """Test a complete signup and unregister cycle"""
        email = "cycle@mergington.edu"
        activity = "Debate%20Team"
        
        # Get initial state
        initial = client.get("/activities").json()
        initial_participants = initial["Debate Team"]["participants"].copy()
        
        # Signup
        signup_response = client.post(f"/activities/{activity}/signup?email={email}")
        assert signup_response.status_code == 200
        
        # Verify signup
        after_signup = client.get("/activities").json()
        assert email in after_signup["Debate Team"]["participants"]
        
        # Unregister
        unreg_response = client.post(f"/activities/{activity}/unregister?email={email}")
        assert unreg_response.status_code == 200
        
        # Verify back to initial state
        final = client.get("/activities").json()
        assert final["Debate Team"]["participants"] == initial_participants
