from fastapi.testclient import TestClient
import main

client = TestClient(main.app)


def test_health_check():
    response = client.get('/api/posts/health')
    assert response.status_code == 200
    assert response.json()['status'] == 'ok'


def test_create_and_read_post():
    response = client.post('/api/posts/', json={
        'title': '테스트 글',
        'content': '테스트 내용',
        'password': '1234'
    })
    assert response.status_code == 200
    data = response.json()
    assert data['title'] == '테스트 글'
    post_id = data['id']

    detail_response = client.get(f'/api/posts/{post_id}')
    assert detail_response.status_code == 200
    assert detail_response.json()['id'] == post_id


def test_search_and_pagination():
    client.post('/api/posts/', json={'title': '부산 축제 정보', 'content': '부산 여행', 'password': '1234'})
    client.post('/api/posts/', json={'title': '부산 맛집 추천', 'content': '부산 여행', 'password': '1234'})

    response = client.get('/api/posts/?search=부산&page=1&limit=1')
    assert response.status_code == 200
    payload = response.json()
    assert payload['page'] == 1
    assert len(payload['items']) <= 1


def test_like_endpoint():
    create_response = client.post('/api/posts/', json={'title': '좋아요 테스트', 'content': '좋아요', 'password': '1234'})
    post_id = create_response.json()['id']

    like_response = client.post(f'/api/posts/{post_id}/like', json={'liked': True})
    assert like_response.status_code == 200
    assert like_response.json()['likes'] >= 1


def test_festival_endpoint():
    response = client.get('/api/festivals/?start_date=20260101&end_date=20261231')
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) > 0
