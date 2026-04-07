import requests
import sys
import json
from datetime import datetime, timedelta

class GenZAITester:
    def __init__(self, base_url="https://task-orchestrator-33.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.token = None
        self.user_id = None
        self.tests_run = 0
        self.tests_passed = 0
        self.created_items = {"tasks": [], "notes": [], "events": []}

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=30)
            elif method == 'PATCH':
                response = requests.patch(url, json=data, headers=test_headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=30)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json() if response.text else {}
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test API health"""
        success, response = self.run_test("API Health Check", "GET", "", 200)
        return success

    def test_register(self):
        """Test user registration"""
        test_user_data = {
            "email": "test@genz.ai",
            "password": "TestPass123!",
            "name": "Test User"
        }
        success, response = self.run_test("User Registration", "POST", "auth/register", 200, test_user_data)
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            print(f"✅ Registration successful, token obtained")
            return True
        return False

    def test_login(self):
        """Test user login"""
        login_data = {
            "email": "test@genz.ai",
            "password": "TestPass123!"
        }
        success, response = self.run_test("User Login", "POST", "auth/login", 200, login_data)
        if success and 'token' in response:
            self.token = response['token']
            self.user_id = response.get('user', {}).get('id')
            print(f"✅ Login successful, token obtained")
            return True
        return False

    def test_create_task(self):
        """Test task creation with priority detection"""
        # Test high priority task
        high_priority_task = {
            "title": "URGENT: Fix critical bug ASAP",
            "description": "This is an emergency task that needs immediate attention"
        }
        success, response = self.run_test("Create High Priority Task", "POST", "tasks", 200, high_priority_task)
        if success and response.get('priority') == 'high':
            self.created_items["tasks"].append(response['id'])
            print(f"✅ High priority detected correctly")
        
        # Test medium priority task
        medium_task = {
            "title": "Review code changes",
            "description": "Regular code review task"
        }
        success, response = self.run_test("Create Medium Priority Task", "POST", "tasks", 200, medium_task)
        if success:
            self.created_items["tasks"].append(response['id'])
            
        return success

    def test_get_tasks(self):
        """Test getting user tasks"""
        success, response = self.run_test("Get Tasks", "GET", "tasks", 200)
        if success and isinstance(response, list):
            print(f"✅ Retrieved {len(response)} tasks")
            return True
        return False

    def test_update_task(self):
        """Test task status update"""
        if not self.created_items["tasks"]:
            print("❌ No tasks to update")
            return False
            
        task_id = self.created_items["tasks"][0]
        update_data = {"status": "completed"}
        success, response = self.run_test("Update Task Status", "PATCH", f"tasks/{task_id}", 200, update_data)
        return success

    def test_delete_task(self):
        """Test task deletion"""
        if len(self.created_items["tasks"]) < 2:
            print("❌ Not enough tasks to delete")
            return False
            
        task_id = self.created_items["tasks"][1]
        success, response = self.run_test("Delete Task", "DELETE", f"tasks/{task_id}", 200)
        if success:
            self.created_items["tasks"].remove(task_id)
        return success

    def test_create_note(self):
        """Test note creation"""
        note_data = {
            "title": "Test Note",
            "content": "This is a test note for the GenZ AI system. It contains important information about productivity."
        }
        success, response = self.run_test("Create Note", "POST", "notes", 200, note_data)
        if success:
            self.created_items["notes"].append(response['id'])
        return success

    def test_get_notes(self):
        """Test getting user notes"""
        success, response = self.run_test("Get Notes", "GET", "notes", 200)
        if success and isinstance(response, list):
            print(f"✅ Retrieved {len(response)} notes")
            return True
        return False

    def test_delete_note(self):
        """Test note deletion"""
        if not self.created_items["notes"]:
            print("❌ No notes to delete")
            return False
            
        note_id = self.created_items["notes"][0]
        success, response = self.run_test("Delete Note", "DELETE", f"notes/{note_id}", 200)
        if success:
            self.created_items["notes"].remove(note_id)
        return success

    def test_create_event(self):
        """Test calendar event creation"""
        start_time = (datetime.now() + timedelta(hours=1)).isoformat()
        end_time = (datetime.now() + timedelta(hours=2)).isoformat()
        
        event_data = {
            "title": "Test Meeting",
            "description": "Important team meeting",
            "start_time": start_time,
            "end_time": end_time
        }
        success, response = self.run_test("Create Event", "POST", "events", 200, event_data)
        if success:
            self.created_items["events"].append(response['id'])
        return success

    def test_get_events(self):
        """Test getting user events"""
        success, response = self.run_test("Get Events", "GET", "events", 200)
        if success and isinstance(response, list):
            print(f"✅ Retrieved {len(response)} events")
            return True
        return False

    def test_delete_event(self):
        """Test event deletion"""
        if not self.created_items["events"]:
            print("❌ No events to delete")
            return False
            
        event_id = self.created_items["events"][0]
        success, response = self.run_test("Delete Event", "DELETE", f"events/{event_id}", 200)
        if success:
            self.created_items["events"].remove(event_id)
        return success

    def test_chat_task_agent(self):
        """Test chat with task-related query"""
        chat_data = {"message": "What are my high priority tasks?"}
        success, response = self.run_test("Chat - Task Agent", "POST", "chat", 200, chat_data)
        if success and response.get('agent_used') == 'task_agent':
            print(f"✅ Task agent correctly invoked")
            return True
        return success

    def test_chat_schedule_agent(self):
        """Test chat with schedule-related query"""
        chat_data = {"message": "Create a daily plan for today"}
        success, response = self.run_test("Chat - Schedule Agent", "POST", "chat", 200, chat_data)
        if success and response.get('agent_used') == 'schedule_agent':
            print(f"✅ Schedule agent correctly invoked")
            return True
        return success

    def test_chat_notes_agent(self):
        """Test chat with notes-related query"""
        chat_data = {"message": "Summarize my notes"}
        success, response = self.run_test("Chat - Notes Agent", "POST", "chat", 200, chat_data)
        if success and response.get('agent_used') == 'notes_agent':
            print(f"✅ Notes agent correctly invoked")
            return True
        return success

    def test_chat_coordinator_agent(self):
        """Test chat with general query"""
        chat_data = {"message": "What should I do next?"}
        success, response = self.run_test("Chat - Coordinator Agent", "POST", "chat", 200, chat_data)
        if success and response.get('agent_used') == 'coordinator_agent':
            print(f"✅ Coordinator agent correctly invoked")
            return True
        return success

    def test_agent_logs(self):
        """Test getting agent activity logs"""
        success, response = self.run_test("Get Agent Logs", "GET", "agent-logs", 200)
        if success and isinstance(response, list):
            print(f"✅ Retrieved {len(response)} agent logs")
            return True
        return False

def main():
    print("🚀 Starting GenZ AI Multi-Agent System Tests")
    print("=" * 50)
    
    tester = GenZAITester()
    
    # Test sequence
    tests = [
        ("API Health Check", tester.test_health_check),
        ("User Registration", tester.test_register),
        ("User Login", tester.test_login),
        ("Create Task", tester.test_create_task),
        ("Get Tasks", tester.test_get_tasks),
        ("Update Task", tester.test_update_task),
        ("Delete Task", tester.test_delete_task),
        ("Create Note", tester.test_create_note),
        ("Get Notes", tester.test_get_notes),
        ("Delete Note", tester.test_delete_note),
        ("Create Event", tester.test_create_event),
        ("Get Events", tester.test_get_events),
        ("Delete Event", tester.test_delete_event),
        ("Chat - Task Agent", tester.test_chat_task_agent),
        ("Chat - Schedule Agent", tester.test_chat_schedule_agent),
        ("Chat - Notes Agent", tester.test_chat_notes_agent),
        ("Chat - Coordinator Agent", tester.test_chat_coordinator_agent),
        ("Agent Activity Logs", tester.test_agent_logs)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if failed_tests:
        print(f"\n❌ Failed tests:")
        for test in failed_tests:
            print(f"  - {test}")
    else:
        print("\n✅ All tests passed!")
    
    success_rate = (tester.tests_passed / tester.tests_run * 100) if tester.tests_run > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())