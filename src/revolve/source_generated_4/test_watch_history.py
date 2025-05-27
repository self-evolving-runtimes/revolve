import json
import uuid
from datetime import datetime, timedelta
import pytest
from falcon import testing

from api import app

def generate_uuid():
    return str(uuid.uuid4())

def now_iso():
    return datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'

@pytest.fixture
def client():
    return testing.TestClient(app)

@pytest.fixture
def sample_watch_history_payload():
    """Generate a valid payload for watch_history."""
    return {
        "id": generate_uuid(),
        "customer_id": generate_uuid(),
        "movie_id": generate_uuid(),
        "device": "web",
        "progress_percent": 55,
        "metadata": {"quality": "HD", "lang": "en"},
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "watched_at": now_iso(),
    }

# 1. Test Create (POST) watch_history
def test_create_watch_history(client, sample_watch_history_payload):
    response = client.simulate_post(
        "/watch_history",
        headers={"X-Test-Request": "true"},
        body=json.dumps(sample_watch_history_payload),
    )
    print(response.content)
    assert response.status == "201 Created"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "success"
    assert resp_json["id"] == sample_watch_history_payload["id"]

# 2. Test Read (GET) single watch_history by id
def test_get_watch_history_by_id(client, sample_watch_history_payload):
    # Create first
    client.simulate_post(
        "/watch_history",
        headers={"X-Test-Request": "true"},
        body=json.dumps(sample_watch_history_payload),
    )
    # Get
    response = client.simulate_get(
        f"/watch_history/{sample_watch_history_payload['id']}",
        headers={"X-Test-Request": "true"},
    )
    print(response.content)
    assert response.status == "200 OK"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "success"
    data = resp_json["data"]
    assert data["id"] == sample_watch_history_payload["id"]
    assert data["customer_id"] == sample_watch_history_payload["customer_id"]
    assert data["movie_id"] == sample_watch_history_payload["movie_id"]
    assert data["device"] == sample_watch_history_payload["device"]
    assert data["progress_percent"] == sample_watch_history_payload["progress_percent"]
    assert data["metadata"] == sample_watch_history_payload["metadata"]

# 3. Test Update (PATCH) partial update
@pytest.mark.parametrize("field,value", [
    ("device", "mobile"),
    ("progress_percent", 99),
    ("metadata", {"quality": "4K"}),
])
def test_patch_watch_history_partial(client, sample_watch_history_payload, field, value):
    # Create first
    client.simulate_post(
        "/watch_history",
        headers={"X-Test-Request": "true"},
        body=json.dumps(sample_watch_history_payload),
    )
    patch_payload = {field: value}
    response = client.simulate_patch(
        f"/watch_history/{sample_watch_history_payload['id']}",
        headers={"X-Test-Request": "true"},
        body=json.dumps(patch_payload),
    )
    print(response.content)
    assert response.status == "200 OK"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "success"
    # Confirm update
    get_resp = client.simulate_get(
        f"/watch_history/{sample_watch_history_payload['id']}",
        headers={"X-Test-Request": "true"},
    )
    data = json.loads(get_resp.content)["data"]
    if field == "metadata":
        assert data[field] == value
    else:
        assert data[field] == value

# 4. Test Delete (DELETE) watch_history by id
def test_delete_watch_history(client, sample_watch_history_payload):
    # Create first
    client.simulate_post(
        "/watch_history",
        headers={"X-Test-Request": "true"},
        body=json.dumps(sample_watch_history_payload),
    )
    # Delete
    response = client.simulate_delete(
        f"/watch_history/{sample_watch_history_payload['id']}",
        headers={"X-Test-Request": "true"},
    )
    print(response.content)
    assert response.status == "200 OK"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "success"
    # Confirm deleted
    get_resp = client.simulate_get(
        f"/watch_history/{sample_watch_history_payload['id']}",
        headers={"X-Test-Request": "true"},
    )
    assert get_resp.status == "404 Not Found"

# 5. Test List (GET) with filtering, pagination, and sorting
@pytest.mark.parametrize("count,skip,limit,order", [
    (3, 0, 2, "asc"),
    (3, 1, 2, "desc"),
])
def test_list_watch_history_pagination_sort(client, count, skip, limit, order):
    # Insert multiple records
    ids = []
    customer_id = generate_uuid()
    movie_id = generate_uuid()
    for i in range(count):
        payload = {
            "id": generate_uuid(),
            "customer_id": customer_id,
            "movie_id": movie_id,
            "device": f"device_{i}",
            "progress_percent": 10 + i,
            "metadata": {"idx": i},
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "watched_at": now_iso(),
        }
        ids.append(payload["id"])
        client.simulate_post(
            "/watch_history",
            headers={"X-Test-Request": "true"},
            body=json.dumps(payload),
        )
    # List with filter
    response = client.simulate_get(
        f"/watch_history?customer_id={customer_id}&movie_id={movie_id}&skip={skip}&limit={limit}&sort=progress_percent&order={order}",
        headers={"X-Test-Request": "true"},
    )
    print(response.content)
    assert response.status == "200 OK"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "success"
    assert resp_json["skip"] == skip
    assert resp_json["limit"] == limit
    assert resp_json["total"] == count
    # Data structure
    data = resp_json["data"]
    assert isinstance(data, list)
    for item in data:
        assert "id" in item and "customer_id" in item and "movie_id" in item
        assert isinstance(item["progress_percent"], int)
        assert isinstance(item["metadata"], dict)
    # Sorting check
    progress_list = [item["progress_percent"] for item in data]
    if order == "asc":
        assert progress_list == sorted(progress_list)
    else:
        assert progress_list == sorted(progress_list, reverse=True)

# 6. Test List (GET) with date filtering
def test_list_watch_history_date_filter(client):
    customer_id = generate_uuid()
    movie_id = generate_uuid()
    dt1 = (datetime.utcnow() - timedelta(days=2)).replace(microsecond=0)
    dt2 = (datetime.utcnow() - timedelta(days=1)).replace(microsecond=0)
    dt3 = datetime.utcnow().replace(microsecond=0)
    ids = []
    for dt in [dt1, dt2, dt3]:
        payload = {
            "id": generate_uuid(),
            "customer_id": customer_id,
            "movie_id": movie_id,
            "device": "tv",
            "progress_percent": 50,
            "metadata": {"dt": dt.isoformat()},
            "created_at": dt.isoformat() + 'Z',
            "updated_at": dt.isoformat() + 'Z',
            "watched_at": dt.isoformat() + 'Z',
        }
        ids.append(payload["id"])
        client.simulate_post(
            "/watch_history",
            headers={"X-Test-Request": "true"},
            body=json.dumps(payload),
        )
    # Filter for records created after dt2
    response = client.simulate_get(
        f"/watch_history?customer_id={customer_id}&created_at_gt={dt2.isoformat()}Z",
        headers={"X-Test-Request": "true"},
    )
    print(response.content)
    assert response.status == "200 OK"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "success"
    data = resp_json["data"]
    for item in data:
        assert item["customer_id"] == customer_id
        assert datetime.fromisoformat(item["created_at"].replace('Z', '')) > dt2

# 7. Test error on GET non-existent id
def test_get_watch_history_not_found(client):
    fake_id = generate_uuid()
    response = client.simulate_get(
        f"/watch_history/{fake_id}",
        headers={"X-Test-Request": "true"},
    )
    print(response.content)
    assert response.status == "404 Not Found"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "error"
    assert resp_json["message"] == "Not found"

# 8. Test error on DELETE non-existent id
def test_delete_watch_history_not_found(client):
    fake_id = generate_uuid()
    response = client.simulate_delete(
        f"/watch_history/{fake_id}",
        headers={"X-Test-Request": "true"},
    )
    print(response.content)
    assert response.status == "404 Not Found"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "error"
    assert resp_json["message"] == "Not found"

# 9. Test error on PATCH with no fields
def test_patch_watch_history_no_fields(client, sample_watch_history_payload):
    # Create first
    client.simulate_post(
        "/watch_history",
        headers={"X-Test-Request": "true"},
        body=json.dumps(sample_watch_history_payload),
    )
    # Patch with empty body
    response = client.simulate_patch(
        f"/watch_history/{sample_watch_history_payload['id']}",
        headers={"X-Test-Request": "true"},
        body=json.dumps({}),
    )
    print(response.content)
    assert response.status == "400 Bad Request"
    resp_json = json.loads(response.content)
    assert resp_json["status"] == "error"
    assert resp_json["message"] == "No fields to update"

# 10. Test GET /watch_history/schema endpoint
def test_watch_history_schema(client):
    response = client.simulate_get("/watch_history/schema", headers={"X-Test-Request": "true"})
    print(response.content)
    assert response.status == "200 OK"
    resp_json = json.loads(response.content)
    assert isinstance(resp_json, list)
    field_names = {f["field"] for f in resp_json}
    expected_fields = {"id", "customer_id", "movie_id", "device", "progress_percent", "metadata", "created_at", "updated_at", "watched_at"}
    assert field_names == expected_fields
