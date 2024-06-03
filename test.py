import requests

BASE_URL = 'http://localhost:5080'

def test_session_crud():
    # Create a session
    create_response = requests.post(f'{BASE_URL}/sessions', json={'name': 'Test Session'})
    assert create_response.status_code == 201
    session_id = create_response.json()['id']
    print(f"Created session with ID: {session_id}")

    # Get all sessions
    get_all_response = requests.get(f'{BASE_URL}/sessions')
    assert get_all_response.status_code == 200
    print("All sessions:", get_all_response.json())

    # Get single session
    get_single_response = requests.get(f'{BASE_URL}/sessions/{session_id}')
    assert get_single_response.status_code == 200
    print("Single session:", get_single_response.json())

    # Update the session
    update_response = requests.patch(f'{BASE_URL}/sessions/{session_id}', json={'name': 'Updated Session Name'})
    assert update_response.status_code == 200
    print("Updated session:", update_response.json())

    # Delete the session
    delete_response = requests.delete(f'{BASE_URL}/sessions/{session_id}')
    assert delete_response.status_code == 200
    print("Deleted session:", delete_response.json())
    print("Test successful!")

if __name__ == '__main__':
    test_session_crud()
