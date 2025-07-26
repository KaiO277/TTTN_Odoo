# XinkJob API Documentation

## Model: xink.job

Quản lý công việc check-in của nhân viên với thông tin địa điểm và shop.

### Fields:
- `employee_id`: ID nhân viên (required)
- `longitude`: Kinh độ GPS 
- `latitude`: Vĩ độ GPS
- `check_in`: Thời gian check-in (required, default: now)
- `shop_name`: Tên shop (required)
- `shop_owner_name`: Tên chủ shop
- `phone_number`: Số điện thoại
- `potential_customer`: Khách hàng tiềm năng (boolean)
- `job_content`: Nội dung công việc
- `job_note`: Ghi chú công việc
- `display_name`: Địa chỉ từ GPS (auto-generated via Nominatim API)
## API Endpoints

### 1. Create Job Check-in
**POST** `/api/job/checkin`

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:**
```json
{
    "longitude": 106.682709,
    "latitude": 10.759972,
    "checkIn": "2025-07-19T08:30:00Z",
    "shopName": "Cửa hàng ABC",
    "shopOwnerName": "Nguyễn Văn A",
    "phoneNumber": "0123456789",
    "potentialCustomer": true,
    "jobContent": "Tư vấn sản phẩm mới",
    "jobNote": "Khách hàng quan tâm đến gói premium"
}
```

**Response:**
```json
{
    "message": "Job check-in created successfully",
    "data": {
        "id": 1,
        "employeeId": 5,
        "employeeName": "Nguyễn Văn B",
        "longitude": 106.682709,
        "latitude": 10.759972,
        "checkIn": "2025-07-19T08:30:00Z",
        "shopName": "Cửa hàng ABC",
        "shopOwnerName": "Nguyễn Văn A",
        "phoneNumber": "0123456789",
        "potentialCustomer": true,
        "jobContent": "Tư vấn sản phẩm mới",
        "jobNote": "Khách hàng quan tâm đến gói premium",
        "locationDisplay": "10.759972, 106.682709",
        "displayName": "123 Nguyễn Huệ, Phường Bến Nghé, Quận 1, Thành phố Hồ Chí Minh, 70000, Việt Nam"
    }
}
```

### 2. Get Job List
**GET** `/api/job/list`

**Query Parameters:**
- `page`: Trang (default: 1)
- `limit`: Số lượng/trang (default: 20)
- `dateFrom`: Từ ngày (YYYY-MM-DD)
- `dateTo`: Đến ngày (YYYY-MM-DD)

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
    "message": "Jobs retrieved successfully",
    "data": {
        "results": [
            {
                "id": 1,
                "employeeId": 5,
                "employeeName": "Nguyễn Văn B",
                "longitude": 106.682709,
                "latitude": 10.759972,
                "checkIn": "2025-07-19T08:30:00Z",
                "shopName": "Cửa hàng ABC",
                "shopOwnerName": "Nguyễn Văn A",
                "phoneNumber": "0123456789",
                "potentialCustomer": true,
                "jobContent": "Tư vấn sản phẩm mới",
                "jobNote": "Khách hàng quan tâm đến gói premium",
                "locationDisplay": "10.759972, 106.682709"
            }
        ],
        "page": 1,
        "limit": 20,
        "total": 50,
        "totalPages": 3
    }
}
```

### 3. Get Job Detail
**GET** `/api/job/<job_id>`

**Headers:**
```
Authorization: Bearer <token>
```

**Response:** Same format as create job response

### 4. Update Job
**PUT** `/api/job/<job_id>`

**Headers:**
```
Authorization: Bearer <token>
Content-Type: application/json
```

**Body:** Same format as create job (all fields optional)

**Response:** Same format as create job response

### 5. Delete Job
**DELETE** `/api/job/<job_id>`

**Headers:**
```
Authorization: Bearer <token>
```

**Response:**
```json
{
    "message": "Job deleted successfully",
    "data": {
        "id": 1
    }
}
```