"""Unit tests for running helper app."""
#TODO move to appropriate file structure
import pytest
from server import retrieve_valid_access_code, refresh_tokens, update_tokens_in_db, process_new_event, send_email
from crud import user_has_active_access_token, get_access_token, get_refresh_token

# Mocking the dependencies of retrieve_valid_access_code
@pytest.fixture
def mock_user_has_active_access_token(mocker):
    return mocker.patch('crud.user_has_active_access_token')

@pytest.fixture
def mock_get_access_token(mocker):
    return mocker.patch('crud.get_access_token')

@pytest.fixture
def mock_get_refresh_token(mocker):
    return mocker.patch('crud.get_refresh_token')

# Test cases
def test_retrieve_valid_access_code_existing_token(mocker,
                                                    mock_user_has_active_access_token,
                                                    mock_get_access_token,
                                                    mock_get_refresh_token):
    # Mocking that the user has an active access token
    mock_user_has_active_access_token.return_value = True

    # Mocking the retrieval of the access token
    mock_access_token = mocker.Mock(code='valid_access_code')
    mock_get_access_token.return_value = mock_access_token

    # Call the function
    access_code = retrieve_valid_access_code(123)  # Assuming user_id is 123

    # Assertions
    assert access_code == 'valid_access_code'
    mock_user_has_active_access_token.assert_called_once_with(123)
    mock_get_access_token.assert_called_once_with(123)
    mock_get_refresh_token.assert_not_called()

# def test_retrieve_valid_access_code_refresh_token(mocker,
#                                                   mock_user_has_active_access_token,
#                                                   mock_get_access_token,
#                                                   mock_get_refresh_token):
#     # Mocking that the user does not have an active access token
#     mock_user_has_active_access_token.return_value = False

#     # Mocking the retrieval of the refresh token
#     mock_refresh_token = mocker.Mock(code='refresh_token')
#     mock_get_refresh_token.return_value = mock_refresh_token

#     # Mocking the retrieval of the new access token
#     mock_new_access_token = mocker.Mock(code='new_access_code')
#     mock_get_access_token.return_value = mock_new_access_token

#     # Call the function
#     access_code = retrieve_valid_access_code(123)  # Assuming user_id is 123

#     # Assertions
#     assert access_code == 'new_access_code'
#     mock_user_has_active_access_token.assert_called_once_with(123)
#     mock_get_refresh_token.assert_called_once_with(123)
#     mock_get_access_token.assert_called_once_with(123)

@pytest.fixture
def mock_get_user_by_strava_id(mocker):
    return mocker.patch('crud.get_user_by_strava_id')

@pytest.fixture
def mock_retrieve_valid_access_code(mocker):
    return mocker.patch('server.retrieve_valid_access_code')

@pytest.fixture
def mock_send_email(mocker):
    return mocker.patch('server.send_email')

def test_process_new_event(mocker,
                            mock_get_user_by_strava_id, 
                            mock_retrieve_valid_access_code, 
                            mock_send_email):
    # Simulated event data
    event_data = {
        'owner_id': 'strava_user_id',
        'gear_id': 'strava_gear_id',
        'object_type': '',
        'aspect_type': '', 
        'object_id': ''
    }

    # Mock database and external dependencies
    mock_user = mocker.Mock(id=123)  # Simulate user data
    mock_get_user_by_strava_id.return_value = mock_user
    mock_retrieve_valid_access_code.return_value = 'access_token'

    # Call the function
    process_new_event(event_data, 'test@example.com', 'default_shoe_strava_id', 'default_shoe_name', 'access_token')

    # Assertions
    # Verify that database functions are called correctly
    mock_get_user_by_strava_id.assert_called_once_with('strava_user_id')
    mock_retrieve_valid_access_code.assert_called_once_with(123)
    # Verify that email is sent
    mock_send_email.assert_called_once_with('test@example.com', 'Run', 'default_shoe_name', 'activity_date')
    # TODO Additional assertions

def test_send_email(mocker):
    mock_send = mocker.patch('server.mail.send')
    send_email('test@example.com', 'Run', 'Test Shoe', '02/16')

    # assert that mail.send was called once
    mock_send.assert_called_once()

    # retrieve arguments
    args, _ = mock_send.call_args
    flask_mail_obj = args[0]
    recipients = flask_mail_obj.recipients
    subject = flask_mail_obj.subject
    body = flask_mail_obj.html 

    # assert that arguments include expected content 
    assert 'test@example.com' in recipients
    assert subject == 'Check your gear on your Run on 02/16'
    assert 'Test Shoe' in body
    assert '02/16' in body