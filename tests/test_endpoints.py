from unittest import mock

from asynctest import CoroutineMock

from neighbour_seeker import db


class TestGetUser:

    async def test_ok(self, client, monkeypatch):
        user_info = {'name': 'test', 'description': None, 'coords': 'POINT(-1 0)'}
        mock_get_user = CoroutineMock()
        mock_get_user.return_value = user_info
        monkeypatch.setattr(db, 'get_user', mock_get_user)
        resp = await client.get('/users/1')
        assert resp.status == 200
        assert await resp.json() == user_info

    async def test_not_found(self, client, monkeypatch):
        user_info = None
        mock_get_user = CoroutineMock()
        mock_get_user.return_value = user_info
        monkeypatch.setattr(db, 'get_user', mock_get_user)
        resp = await client.get('/users/1')
        assert resp.status == 404
        assert await resp.text() == 'User not found'

    async def test_invalid_id(self, client):
        resp = await client.get('/users/invalid')
        assert resp.status == 400
        assert await resp.text() == 'User id must be integer'


class TestCreateUser:

    async def test_ok(self, client, monkeypatch):
        mock_create_user = CoroutineMock()
        mock_create_user.return_value = 123
        monkeypatch.setattr(db, 'create_user', mock_create_user)
        payload = {'name': 'test', 'latitude': 0, 'longitude': -1}
        resp = await client.post('/users', json=payload)
        assert resp.status == 201
        assert await resp.json() == {'user_id': 123}

    async def test_bad_payload(self, client):
        # bad latitude value
        payload = {'name': 'test', 'latitude': 500, 'longitude': -1}
        resp = await client.post('/users', json=payload)
        assert resp.status == 400

    async def test_no_payload(self, client):
        resp = await client.post('/users')
        assert resp.status == 400


class TestUpdateUser:

    async def test_ok(self, client):
        payload = {'name': 'test', 'latitude': 2, 'longitude': -3}
        resp = await client.put('/users/1', json=payload)
        assert resp.status == 200

    async def test_not_found(self, client, monkeypatch):
        mock_get_user = CoroutineMock()
        mock_get_user.return_value = None
        monkeypatch.setattr(db, 'get_user', mock_get_user)
        payload = {'name': 'test', 'description': 'something', 'latitude': 2, 'longitude': -3}
        resp = await client.put('/users/1', json=payload)
        assert resp.status == 404
        assert await resp.text() == 'User not found'

    async def test_invalid_id(self, client):
        resp = await client.put('/users/invalid')
        assert resp.status == 400
        assert await resp.text() == 'User id must be integer'

    async def test_bad_payload(self, client):
        # missing name
        payload = {'latitude': 5, 'longitude': -1}
        resp = await client.put('/users/1', json=payload)
        assert resp.status == 400

    async def test_no_payload(self, client):
        resp = await client.put('/users/1')
        assert resp.status == 400


class TestDeleteUser:

    async def test_ok(self, client):
        resp = await client.delete('/users/1')
        assert resp.status == 200

    async def test_not_found(self, client, monkeypatch):
        mock_get_user = CoroutineMock()
        mock_get_user.return_value = None
        monkeypatch.setattr(db, 'get_user', mock_get_user)
        resp = await client.delete('/users/1')
        assert resp.status == 404
        assert await resp.text() == 'User not found'

    async def test_invalid_id(self, client):
        resp = await client.delete('/users/invalid')
        assert resp.status == 400
        assert await resp.text() == 'User id must be integer'


class TestSearch:

    async def test_ok(self, client, monkeypatch):
        mock_search = CoroutineMock()
        mock_search.return_value = [1, 2, 3]
        monkeypatch.setattr(db, 'search', mock_search)
        payload = {'user_id': 5, 'count': 10, 'distance': 2500}
        resp = await client.post('/search', json=payload)
        # check distance conversion from kilometers to meters (conn is mocked)
        mock_search.assert_awaited_with(mock.ANY, 5, 2500000, 10)
        assert resp.status == 200
        assert await resp.json() == [1, 2, 3]

    async def test_ok_empty(self, client):
        payload = {'user_id': 5, 'count': 10, 'distance': 2500}
        resp = await client.post('/search', json=payload)
        assert resp.status == 200
        assert await resp.json() == []

    async def test_not_found(self, client, monkeypatch):
        mock_get_user = CoroutineMock()
        mock_get_user.return_value = None
        monkeypatch.setattr(db, 'get_user', mock_get_user)
        payload = {'user_id': 2, 'count': 10, 'distance': 2500}
        resp = await client.post('/search', json=payload)
        assert resp.status == 404
        assert await resp.text() == 'User not found'

    async def test_bad_payload(self, client):
        # bad distance value
        payload = {'user_id': 2, 'count': 10, 'distance': 'very long'}
        resp = await client.post('/search', json=payload)
        assert resp.status == 400

    async def test_no_payload(self, client):
        resp = await client.post('/search')
        assert resp.status == 400
