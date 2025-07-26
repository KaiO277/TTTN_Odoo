# Mail Activity API Documentation

## Overview
API để quản lý Mail Activities và Hash Tags với authentication và filtering nâng cao.

## Base URLs
- Mail Activities: `/api/mail-activities`
- Hash Tags: `/api/hash-tags`

## Authentication
Tất cả endpoints yêu cầu JWT token trong header hoặc query parameter.
- Token được validate thông qua `xink_check_auth_and_company()`
- Chỉ user đã authenticate mới có thể truy cập activities và hash tags của mình

---

## Mail Activity Endpoints

### 1. GET - Lấy danh sách activities

**Endpoint:** `GET /api/mail-activities`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters:**
- `page` (int, optional): Số trang (default: 1)
- `limit` (int, optional): Số lượng items per page (default: 20)
- `search` (string, optional): Tìm kiếm theo summary hoặc note
- `hashTags` (array, optional): Filter theo hash tag IDs (JSON array)
- `type` (string, optional): Loại activity filter
  - `all` - Tất cả activities (default)
  - `assigned` - Activities được gán cho user (không phải tự tạo)
  - `created` - Activities do user tạo ra
- `status` (string, optional): Trạng thái activity filter
  - `all` - Tất cả trạng thái (default)
  - `done` - Activities đã hoàn thành
  - `notDone` - Activities chưa hoàn thành
  - `overdue` - Activities quá hạn
  - `importantWork` - Activities important work
- `dateFrom` (string, optional): Lọc từ ngày (YYYY-MM-DD)
- `dateTo` (string, optional): Lọc đến ngày (YYYY-MM-DD)

**Example Request:**
```bash
GET /api/mail-activities?page=1&limit=10&type=assigned&status=notDone&search=client&hashTags=[1,2,3]&dateFrom=2025-01-01&dateTo=2025-01-31
```

**Example Response:**
```json
{
  "success": true,
  "message": "Successfully",
  "data": {
    "results": [
      {
        "id": 1,
        "summary": "Follow up with client",
        "note": "Need to discuss contract details",
        "activityTypeId": 2,
        "activityTypeName": "Call",
        "resName": "ABC Company",
        "resModel": "res.partner",
        "resId": 15,
        "userId": 1,
        "userName": "John Doe",
        "dateDeadline": "2025-01-25",
        "dateDone": null,
        "active": true,
        "hashTags": [
          {
            "id": 1,
            "name": "urgent",
            "color": "#FF0000"
          },
          {
            "id": 2,
            "name": "important",
            "color": "#FFA500"
          }
        ],
        "importantWork": true,
        "createDate": "2025-01-20 10:30:00",
        "writeDate": "2025-01-20 10:30:00"
      }
    ],
    "page": 1,
    "limit": 10,
    "total": 25,
    "totalPages": 3
  }
}
```

---

### 2. GET - Lấy activity theo ID

**Endpoint:** `GET /api/mail-activities/{id}`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Example Request:**
```bash
GET /api/mail-activities/1
```

**Example Response:**
```json
{
  "success": true,
  "message": "Successfully",
  "data": {
    "id": 1,
    "summary": "Follow up with client",
    "note": "Need to discuss contract details",
    "activityTypeId": 2,
    "activityTypeName": "Call",
    "resName": "ABC Company",
    "resModel": "res.partner",
    "resId": 15,
    "userId": 1,
    "userName": "John Doe",
    "dateDeadline": "2025-01-25",
    "dateDone": null,
    "active": true,
    "hashTags": [
      {
        "id": 1,
        "name": "urgent",
        "color": "#FF0000"
      },
      {
        "id": 2,
        "name": "important",
        "color": "#FFA500"
      }
    ],
    "importantWork": true,
    "createDate": "2025-01-20 10:30:00",
    "writeDate": "2025-01-20 10:30:00"
  }
}
```

---

### 3. POST - Tạo activity mới

**Endpoint:** `POST /api/mail-activities`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
Content-Type: application/json
```

**Request Body:**
```json
{
  "summary": "New activity summary",
  "note": "Activity description",
  "dateDeadline": "2025-01-30",
  "hashTags": [
    {
      "name": "urgent",
      "color": "#FF0000"
    },
    {
      "name": "follow-up",
      "color": "#0066CC"
    }
  ],
  "importantWork": false
}
```

**Example Response:**
```json
{
  "success": true,
  "message": "Successfully"
}
```

**Note:** 
- Activity được tạo với user hiện tại
- Tự động gán vào res.partner (ID=3) và activity_type_id=4
- res_model được set thành 'res.partner'

---

### 4. PUT - Đánh dấu hoàn thành

**Endpoint:** `PUT /api/mail-activities/action_done/{id}`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Example Request:**
```bash
PUT /api/mail-activities/action_done/1
```

**Example Response:**
```json
{
  "success": true,
  "message": "Successfully"
}
```

**Description:**
- Gọi method `action_done()` của Odoo để đánh dấu activity hoàn thành
- Chỉ owner của activity mới có thể thực hiện action này

---

### 5. DELETE - Xóa activity

**Endpoint:** `DELETE /api/mail-activities/{id}`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Example Request:**
```bash
DELETE /api/mail-activities/1
```

**Example Response:**
```json
{
  "success": true,
  "message": "Successfully"
}
```

**Description:**
- Xóa hoàn toàn activity khỏi database
- Chỉ owner của activity mới có thể xóa

---

## Hash Tag Management Endpoints

### 6. GET - Lấy danh sách hash tags

**Endpoint:** `GET /api/hash-tags`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Query Parameters:**
- `page` (int, optional): Số trang (default: 1)
- `limit` (int, optional): Số lượng items per page (default: 100)
- `search` (string, optional): Tìm kiếm theo tên tag

**Example Request:**
```bash
GET /api/hash-tags?page=1&limit=20&search=urgent
```

**Example Response:**
```json
{
  "message": "Successfully",
  "data": {
    "results": [
      {
        "id": 1,
        "name": "urgent",
        "color": 1,
        "description": "Urgent tasks",
        "activityCount": 5,
        "active": true
      },
      {
        "id": 2,
        "name": "meeting",
        "color": 2,
        "description": "Meeting related",
        "activityCount": 10,
        "active": true
      }
    ],
    "page": 1,
    "limit": 20,
    "total": 2,
    "totalPages": 1
  }
}
```
