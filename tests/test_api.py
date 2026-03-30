"""
API Test Suite for IT Asset Inventory Management System
Run with: pytest test_api.py -v
"""

import pytest
import requests
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test credentials
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123",
    "full_name": "Test User"
}

# Global token storage
token = None

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_user(self):
        """Test user registration"""
        response = requests.post(
            f"{BASE_URL}/api/auth/register",
            json=TEST_USER
        )
        assert response.status_code in [200, 400]  # 400 if user exists
        
        if response.status_code == 200:
            data = response.json()
            assert "access_token" in data
            global token
            token = data["access_token"]
    
    def test_login(self):
        """Test user login"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "username": TEST_USER["username"],
                "password": TEST_USER["password"]
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        
        global token
        token = data["access_token"]
    
    def test_get_current_user(self):
        """Test getting current user info"""
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "username" in data


class TestEquipment:
    """Test equipment endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup headers for all tests"""
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def test_create_equipment(self):
        """Test creating equipment"""
        equipment_data = {
            "asset_no": f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "serial_no": "SN123456",
            "product_name": "Test Laptop",
            "category": "Computers",
            "status": "Available",
            "location": "Test Room",
            "cost": 1000.00
        }
        
        response = requests.post(
            f"{BASE_URL}/api/equipment",
            headers=self.headers,
            json=equipment_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["asset_no"] == equipment_data["asset_no"]
    
    def test_get_equipment(self):
        """Test retrieving equipment list"""
        response = requests.get(
            f"{BASE_URL}/api/equipment",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_search_equipment(self):
        """Test autocomplete search"""
        response = requests.get(
            f"{BASE_URL}/api/equipment/search/TEST",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_filter_equipment(self):
        """Test filtering equipment"""
        response = requests.get(
            f"{BASE_URL}/api/equipment",
            headers=self.headers,
            params={"category": "Computers", "status": "Available"}
        )
        assert response.status_code == 200


class TestStatistics:
    """Test statistics endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup headers for all tests"""
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def test_overview_stats(self):
        """Test overview statistics"""
        response = requests.get(
            f"{BASE_URL}/api/stats/overview",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "available" in data
    
    def test_category_stats(self):
        """Test category statistics"""
        response = requests.get(
            f"{BASE_URL}/api/stats/category",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestImport:
    """Test CSV import functionality"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup headers for all tests"""
        self.headers = {"Authorization": f"Bearer {token}"}
    
    def test_get_imports(self):
        """Test retrieving import history"""
        response = requests.get(
            f"{BASE_URL}/api/imports",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
