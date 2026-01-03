"""
Tests for Android MT5 Connector

Tests the Android-specific MT5 connector functionality including:
- Platform detection
- Connector factory
- Android connector basic operations
- Bridge communication
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cthulu.utils.platform_detector import (
    detect_termux,
    detect_android,
    get_platform_type,
    get_platform_info,
    is_android,
    is_windows
)
from cthulu.connector.factory import create_connector, get_connector_type
from cthulu.connector.mt5_connector_android import MT5ConnectorAndroid, AndroidConnectionConfig


class TestPlatformDetection:
    """Tests for platform detection utilities."""
    
    def test_detect_termux_with_env_var(self):
        """Test Termux detection via environment variable."""
        with patch.dict(os.environ, {'TERMUX_VERSION': '0.118'}):
            assert detect_termux() is True
    
    def test_detect_termux_without_indicators(self):
        """Test Termux detection without indicators."""
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.path.exists', return_value=False):
                assert detect_termux() is False
    
    def test_detect_android_via_termux(self):
        """Test Android detection via Termux."""
        with patch('cthulu.utils.platform_detector.detect_termux', return_value=True):
            assert detect_android() is True
    
    def test_get_platform_type_windows(self):
        """Test platform type detection for Windows."""
        with patch('sys.platform', 'win32'):
            with patch('cthulu.utils.platform_detector.detect_android', return_value=False):
                assert get_platform_type() == "windows"
    
    def test_get_platform_type_linux(self):
        """Test platform type detection for Linux."""
        with patch('sys.platform', 'linux'):
            with patch('cthulu.utils.platform_detector.detect_android', return_value=False):
                assert get_platform_type() == "linux"
    
    def test_get_platform_type_android(self):
        """Test platform type detection for Android."""
        with patch('cthulu.utils.platform_detector.detect_android', return_value=True):
            assert get_platform_type() == "android"
    
    def test_get_platform_info(self):
        """Test comprehensive platform info retrieval."""
        info = get_platform_info()
        
        assert info is not None
        assert info.platform_type in ["windows", "linux", "android", "macos", "unknown"]
        assert isinstance(info.is_android, bool)
        assert isinstance(info.is_windows, bool)
        assert isinstance(info.is_linux, bool)
        assert info.system is not None
        assert info.python_version is not None


class TestConnectorFactory:
    """Tests for connector factory."""
    
    def test_get_connector_type_android(self):
        """Test getting connector type for Android."""
        assert get_connector_type('android') == 'android'
    
    def test_get_connector_type_windows(self):
        """Test getting connector type for Windows."""
        assert get_connector_type('windows') == 'standard'
    
    def test_get_connector_type_linux(self):
        """Test getting connector type for Linux."""
        assert get_connector_type('linux') == 'standard'
    
    def test_create_connector_force_android(self):
        """Test creating Android connector with force_platform."""
        config = {
            'login': 12345,
            'password': 'test',
            'server': 'TestServer',
            'bridge_host': '127.0.0.1',
            'bridge_port': 18812
        }
        
        connector = create_connector(config, force_platform='android')
        
        assert isinstance(connector, MT5ConnectorAndroid)
        assert connector.config.login == 12345
        assert connector.config.bridge_port == 18812
    
    def test_create_connector_auto_windows(self):
        """Test auto-creating Windows connector."""
        from cthulu.connector.mt5_connector import MT5Connector
        
        config = {
            'login': 12345,
            'password': 'test',
            'server': 'TestServer'
        }
        
        with patch('sys.platform', 'win32'):
            with patch('cthulu.utils.platform_detector.detect_android', return_value=False):
                connector = create_connector(config)
                
                assert isinstance(connector, MT5Connector)


class TestAndroidConnector:
    """Tests for Android MT5 connector."""
    
    @pytest.fixture
    def android_config(self):
        """Create test Android config."""
        return AndroidConnectionConfig(
            bridge_host='127.0.0.1',
            bridge_port=18812,
            bridge_type='rest',
            login=12345,
            password='test',
            server='TestServer'
        )
    
    @pytest.fixture
    def android_connector(self, android_config):
        """Create test Android connector."""
        return MT5ConnectorAndroid(android_config)
    
    def test_connector_initialization(self, android_connector):
        """Test connector initialization."""
        assert android_connector is not None
        assert android_connector.connected is False
        assert android_connector.config.bridge_port == 18812
    
    def test_check_rest_bridge_success(self, android_connector):
        """Test REST bridge availability check - success."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch('requests.get', return_value=mock_response):
            result = android_connector._check_rest_bridge()
            assert result is True
    
    def test_check_rest_bridge_failure(self, android_connector):
        """Test REST bridge availability check - failure."""
        with patch('requests.get', side_effect=Exception('Connection refused')):
            result = android_connector._check_rest_bridge()
            assert result is False
    
    def test_check_socket_bridge(self, android_connector):
        """Test socket bridge availability check."""
        with patch('socket.socket') as mock_socket:
            mock_sock_instance = Mock()
            mock_sock_instance.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock_instance
            
            result = android_connector._check_socket_bridge()
            assert result is True
    
    def test_send_rest_request_success(self, android_connector):
        """Test sending REST request - success."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'success': True, 'data': {'balance': 10000}}
        
        with patch('requests.post', return_value=mock_response):
            result = android_connector._send_rest_request('account_info', {})
            
            assert result is not None
            assert result['success'] is True
            assert result['data']['balance'] == 10000
    
    def test_send_rest_request_failure(self, android_connector):
        """Test sending REST request - failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.text = 'Internal server error'
        
        with patch('requests.post', return_value=mock_response):
            result = android_connector._send_rest_request('account_info', {})
            
            assert result is None
    
    def test_connect_bridge_not_available(self, android_connector):
        """Test connection when bridge is not available."""
        with patch.object(android_connector, '_check_bridge_available', return_value=False):
            result = android_connector.connect()
            
            assert result is False
            assert android_connector.connected is False
    
    def test_connect_success(self, android_connector):
        """Test successful connection."""
        with patch.object(android_connector, '_check_bridge_available', return_value=True):
            with patch.object(android_connector, '_send_bridge_request') as mock_send:
                # Mock initialize response
                mock_send.side_effect = [
                    {'success': True},  # initialize
                    {'success': True, 'data': {'login': 12345, 'balance': 10000, 'server': 'TestServer'}}  # account_info
                ]
                
                result = android_connector.connect()
                
                assert result is True
                assert android_connector.connected is True
    
    def test_disconnect(self, android_connector):
        """Test disconnection."""
        android_connector.connected = True
        
        with patch.object(android_connector, '_send_bridge_request', return_value={'success': True}):
            android_connector.disconnect()
            
            assert android_connector.connected is False
    
    def test_is_connected_when_connected(self, android_connector):
        """Test is_connected when actually connected."""
        android_connector.connected = True
        
        with patch.object(android_connector, '_send_bridge_request') as mock_send:
            mock_send.return_value = {'success': True}
            
            result = android_connector.is_connected()
            assert result is True
    
    def test_is_connected_when_not_connected(self, android_connector):
        """Test is_connected when not connected."""
        android_connector.connected = False
        
        result = android_connector.is_connected()
        assert result is False
    
    def test_get_account_info(self, android_connector):
        """Test getting account info."""
        android_connector.connected = True
        
        with patch.object(android_connector, '_send_bridge_request') as mock_send:
            mock_send.return_value = {
                'success': True,
                'data': {
                    'login': 12345,
                    'balance': 10000.0,
                    'equity': 10500.0,
                    'margin': 500.0
                }
            }
            
            result = android_connector.get_account_info()
            
            assert result is not None
            assert result['login'] == 12345
            assert result['balance'] == 10000.0
    
    def test_get_symbol_info(self, android_connector):
        """Test getting symbol info."""
        android_connector.connected = True
        
        with patch.object(android_connector, '_send_bridge_request') as mock_send:
            mock_send.return_value = {
                'success': True,
                'data': {
                    'name': 'EURUSD',
                    'bid': 1.10000,
                    'ask': 1.10010,
                    'spread': 10
                }
            }
            
            result = android_connector.get_symbol_info('EURUSD')
            
            assert result is not None
            assert result['name'] == 'EURUSD'
            assert result['spread'] == 10
    
    def test_get_rates(self, android_connector):
        """Test getting historical rates."""
        android_connector.connected = True
        
        with patch.object(android_connector, '_send_bridge_request') as mock_send:
            mock_send.return_value = {
                'success': True,
                'data': [
                    {
                        'time': '2024-01-01T00:00:00',
                        'open': 1.10000,
                        'high': 1.10050,
                        'low': 1.09950,
                        'close': 1.10020,
                        'tick_volume': 1000,
                        'spread': 10,
                        'real_volume': 100000
                    }
                ]
            }
            
            result = android_connector.get_rates('EURUSD', 16385, 10)  # H1 timeframe
            
            assert result is not None
            assert len(result) == 1
            assert result[0]['close'] == 1.10020
    
    def test_get_open_positions(self, android_connector):
        """Test getting open positions."""
        android_connector.connected = True
        
        with patch.object(android_connector, '_send_bridge_request') as mock_send:
            mock_send.return_value = {
                'success': True,
                'data': [
                    {
                        'ticket': 12345,
                        'symbol': 'EURUSD',
                        'volume': 0.01,
                        'profit': 10.50
                    }
                ]
            }
            
            result = android_connector.get_open_positions()
            
            assert len(result) == 1
            assert result[0]['ticket'] == 12345
            assert result[0]['profit'] == 10.50
    
    def test_health_check(self, android_connector):
        """Test health check."""
        android_connector.connected = True
        
        with patch.object(android_connector, '_send_bridge_request') as mock_send:
            # First call is for terminal_info
            # Second call is for account_info
            def mock_response(method, params):
                if method == 'terminal_info':
                    return {
                        'success': True,
                        'data': {
                            'connected': True,
                            'trade_allowed': True
                        }
                    }
                elif method == 'account_info':
                    return {
                        'success': True,
                        'data': {
                            'trade_allowed': True,
                            'balance': 10000,
                            'equity': 10500,
                            'margin_level': 1000
                        }
                    }
            
            mock_send.side_effect = mock_response
            
            result = android_connector.health_check()
            
            assert result is not None
            assert result['connected'] is True
            assert result['platform'] == 'android'
            assert result['balance'] == 10000
    
    def test_context_manager(self, android_connector):
        """Test context manager protocol."""
        with patch.object(android_connector, 'connect', return_value=True):
            with patch.object(android_connector, 'disconnect'):
                with android_connector as conn:
                    assert conn is android_connector
                
                android_connector.disconnect.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
