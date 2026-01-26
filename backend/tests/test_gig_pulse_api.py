"""
The Gig Pulse API Tests
Tests for YouTube API, Static Content, and Admin functionality
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasicEndpoints:
    """Health check and basic API tests"""
    
    def test_health_check(self):
        """Test health endpoint returns healthy status"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        print(f"✓ Health check passed: {data}")
    
    def test_root_endpoint(self):
        """Test root API endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        print(f"✓ Root endpoint passed: {data}")


class TestYouTubeAPI:
    """YouTube API integration tests"""
    
    def test_youtube_feed(self):
        """Test YouTube feed returns videos"""
        response = requests.get(f"{BASE_URL}/api/youtube/feed")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0, "Feed should have videos"
        # Verify video structure
        video = data["data"][0]
        assert "video_id" in video
        assert "title" in video
        assert "channel_title" in video
        print(f"✓ YouTube feed returned {len(data['data'])} videos")
    
    def test_youtube_featured_channels(self):
        """Test featured channels endpoint"""
        response = requests.get(f"{BASE_URL}/api/youtube/featured-channels")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert len(data["data"]) > 0
        print(f"✓ Featured channels returned {len(data['data'])} channels")
    
    def test_youtube_keywords(self):
        """Test gig keywords endpoint"""
        response = requests.get(f"{BASE_URL}/api/youtube/keywords")
        assert response.status_code == 200
        data = response.json()
        assert "keywords" in data
        assert len(data["keywords"]) > 0
        print(f"✓ Keywords endpoint returned {len(data['keywords'])} keywords")


class TestHideVideoAPI:
    """Admin hide video functionality tests"""
    
    def test_hide_video(self):
        """Test hiding a video"""
        test_video_id = f"test_video_{uuid.uuid4().hex[:8]}"
        response = requests.post(f"{BASE_URL}/api/youtube/hide/{test_video_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "hidden" in data["message"].lower()
        print(f"✓ Hide video passed for {test_video_id}")
        
        # Verify it's in hidden list
        hidden_response = requests.get(f"{BASE_URL}/api/youtube/hidden")
        assert hidden_response.status_code == 200
        hidden_data = hidden_response.json()
        assert test_video_id in hidden_data["data"]
        print(f"✓ Video {test_video_id} found in hidden list")
        
        # Cleanup - unhide the video
        unhide_response = requests.delete(f"{BASE_URL}/api/youtube/hide/{test_video_id}")
        assert unhide_response.status_code == 200
        print(f"✓ Video {test_video_id} unhidden successfully")
    
    def test_get_hidden_videos(self):
        """Test getting list of hidden videos"""
        response = requests.get(f"{BASE_URL}/api/youtube/hidden")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        assert isinstance(data["data"], list)
        print(f"✓ Hidden videos endpoint returned {len(data['data'])} hidden videos")


class TestStaticContentAPI:
    """Static content API tests"""
    
    def test_featured_channels(self):
        """Test featured channels static content"""
        response = requests.get(f"{BASE_URL}/api/static-content/featured-channels")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["data"]) == 3, "Should have 3 featured channels"
        # Verify channel structure
        channel = data["data"][0]
        assert "id" in channel
        assert "name" in channel
        assert "handle" in channel
        assert "thumbnail" in channel
        assert "channelUrl" in channel
        print(f"✓ Featured channels: {[c['name'] for c in data['data']]}")
    
    def test_gig_apps(self):
        """Test gig apps static content"""
        response = requests.get(f"{BASE_URL}/api/static-content/gig-apps")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["data"]) == 10, "Should have 10 gig apps"
        # Verify app structure
        app = data["data"][0]
        assert "id" in app
        assert "name" in app
        assert "icon" in app
        assert "url" in app
        print(f"✓ Gig apps: {[a['name'] for a in data['data']]}")
    
    def test_helpful_tools(self):
        """Test helpful tools static content"""
        response = requests.get(f"{BASE_URL}/api/static-content/helpful-tools")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["data"]) >= 5, "Should have at least 5 helpful tools"
        # Verify tool structure
        tool = data["data"][0]
        assert "id" in tool
        assert "name" in tool
        assert "description" in tool
        assert "features" in tool
        print(f"✓ Helpful tools: {[t['name'] for t in data['data']]}")
    
    def test_featured_gear(self):
        """Test featured gear static content"""
        response = requests.get(f"{BASE_URL}/api/static-content/featured-gear")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["data"]) == 3, "Should have 3 featured gear items"
        # Verify gear structure
        gear = data["data"][0]
        assert "id" in gear
        assert "name" in gear
        assert "price" in gear
        assert "image" in gear
        assert "affiliateUrl" in gear
        print(f"✓ Featured gear: {[g['name'] for g in data['data']]}")
    
    def test_weekly_shows(self):
        """Test weekly shows static content"""
        response = requests.get(f"{BASE_URL}/api/static-content/weekly-shows")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["data"]) >= 3, "Should have at least 3 weekly shows"
        # Verify show structure
        show = data["data"][0]
        assert "id" in show
        assert "name" in show
        assert "schedule" in show
        print(f"✓ Weekly shows: {[s['name'] for s in data['data']]}")
    
    def test_community_favorites(self):
        """Test community favorites static content"""
        response = requests.get(f"{BASE_URL}/api/static-content/community-favorites")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert len(data["data"]) > 0, "Should have community favorites"
        print(f"✓ Community favorites: {len(data['data'])} items")


class TestNewsFeedAPI:
    """News feed API tests"""
    
    def test_news_feed(self):
        """Test news feed endpoint"""
        response = requests.get(f"{BASE_URL}/api/news/feed")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "data" in data
        print(f"✓ News feed returned {len(data.get('data', []))} articles")
    
    def test_news_sources(self):
        """Test news sources endpoint"""
        response = requests.get(f"{BASE_URL}/api/news/sources")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "sources" in data
        print(f"✓ News sources: {len(data['sources'])} sources")


class TestSuggestionsAPI:
    """Suggestions API tests"""
    
    def test_channel_suggestion(self):
        """Test channel suggestion submission"""
        test_data = {
            "name": f"TEST_Channel_{uuid.uuid4().hex[:6]}",
            "url": "https://youtube.com/@testchannel"
        }
        response = requests.post(f"{BASE_URL}/api/suggestions/channel", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["name"] == test_data["name"]
        print(f"✓ Channel suggestion created: {data['id']}")
    
    def test_gear_suggestion(self):
        """Test gear suggestion submission"""
        test_data = {
            "name": f"TEST_Gear_{uuid.uuid4().hex[:6]}",
            "category": "accessories",
            "description": "Test gear item for testing"
        }
        response = requests.post(f"{BASE_URL}/api/suggestions/gear", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ Gear suggestion created: {data['id']}")
    
    def test_app_suggestion(self):
        """Test app suggestion submission"""
        test_data = {
            "name": f"TEST_App_{uuid.uuid4().hex[:6]}",
            "category": "tools",
            "description": "Test app for testing"
        }
        response = requests.post(f"{BASE_URL}/api/suggestions/app", json=test_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        print(f"✓ App suggestion created: {data['id']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
