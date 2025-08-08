#!/usr/bin/env python3
"""
Samsung LHB55ECH Business Display Adapter
Enhanced MDC protocol support for Samsung Business Displays
"""

import asyncio
import socket
import struct
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import time

logger = logging.getLogger(__name__)

class MDCCommand(Enum):
    """Samsung MDC Protocol Commands for LHB55ECH"""
    POWER = 0x11
    VOLUME = 0x12
    MUTE = 0x13
    INPUT_SOURCE = 0x14
    PICTURE_MODE = 0x15
    SOUND_MODE = 0x16
    SAFETY_LOCK = 0x17
    PICTURE_SIZE = 0x18
    AUTO_ADJUSTMENT = 0x19
    WALL_MODE = 0x1A
    SAFETY_SCREEN = 0x1B
    LOGO_DISPLAY = 0x1C
    POWER_ON_DELAY = 0x1D
    POWER_OFF_DELAY = 0x1E
    SOUND_SELECT = 0x1F
    LAMP_CONTROL = 0x20
    PANEL_LOCK = 0x21
    CONTRAST = 0x22
    BRIGHTNESS = 0x23
    SHARPNESS = 0x24
    COLOR = 0x25
    TINT = 0x26
    RED_GAIN = 0x27
    GREEN_GAIN = 0x28
    BLUE_GAIN = 0x29
    RESET = 0x2A
    CURRENT_TEMP = 0x2B
    SERIAL_NUMBER = 0x2C
    SOFTWARE_VERSION = 0x2D
    MODEL_NUMBER = 0x2E
    INPUT_SOURCE_AUTO_SWITCH = 0x2F
    CLOCK_1 = 0x30
    CLOCK_2 = 0x31
    CLOCK_3 = 0x32
    HOLIDAY_APPLY = 0x33
    SCHEDULE_TYPE = 0x34
    HOLIDAY_DELETE = 0x35
    TIMER_1 = 0x36
    TIMER_2 = 0x37
    TIMER_3 = 0x38
    CLONE_SETTINGS = 0x39
    NETWORK_SETTINGS = 0x3A
    OSD_DISPLAY = 0x3B
    VIDEO_WALL_MODE = 0x84
    VIDEO_WALL_USER = 0x89

class InputSource(Enum):
    """Input sources for Samsung LHB55ECH"""
    PC = 0x14
    DVI = 0x18
    DVI_VIDEO = 0x1F
    HDMI = 0x21
    HDMI_PC = 0x22
    HDMI2 = 0x23
    HDMI2_PC = 0x24
    DISPLAY_PORT = 0x25
    DTV = 0x30
    MEDIA_PLAYER_HDMI = 0x60
    MEDIA_PLAYER_DVI = 0x61
    MAGIC_INFO = 0x20

@dataclass
class DisplayCapabilities:
    """Capabilities of Samsung LHB55ECH"""
    model: str = "LHB55ECH"
    screen_size: str = "55 inch"
    resolution: str = "1920x1080"
    brightness: int = 700  # cd/m²
    supported_inputs: List[str] = None
    video_wall_support: bool = True
    max_video_wall_size: str = "10x10"
    network_capable: bool = True
    usb_playback: bool = True
    
    def __post_init__(self):
        if self.supported_inputs is None:
            self.supported_inputs = [
                "HDMI", "HDMI2", "DVI", "Display Port", 
                "PC", "DTV", "MagicInfo", "Media Player"
            ]

class SamsungLHB55ECHAdapter:
    """Enhanced adapter for Samsung LHB55ECH Business Display"""
    
    def __init__(self, display_id: int, ip: str, port: int = 1515):
        self.display_id = display_id
        self.ip = ip
        self.port = port
        self.capabilities = DisplayCapabilities()
        self.connected = False
        self.last_response_time = None
        self.error_count = 0
        self.max_retries = 3
        
    async def connect(self) -> bool:
        """Establish connection to display"""
        try:
            self.reader, self.writer = await asyncio.wait_for(
                asyncio.open_connection(self.ip, self.port),
                timeout=10.0
            )
            self.connected = True
            self.error_count = 0
            logger.info(f"Connected to Samsung LHB55ECH at {self.ip}:{self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to display {self.display_id}: {e}")
            self.connected = False
            return False
    
    async def disconnect(self):
        """Close connection to display"""
        if hasattr(self, 'writer') and self.writer:
            self.writer.close()
            await self.writer.wait_closed()
        self.connected = False
    
    def _create_mdc_packet(self, command: MDCCommand, data: bytes = b'') -> bytes:
        """Create MDC protocol packet"""
        header = 0xAA
        cmd = command.value
        display_id = self.display_id
        data_length = len(data)
        
        # Calculate checksum
        checksum = (header + cmd + display_id + data_length + sum(data)) & 0xFF
        
        packet = struct.pack('BBBB', header, cmd, display_id, data_length)
        packet += data
        packet += struct.pack('B', checksum)
        
        return packet
    
    def _parse_mdc_response(self, response: bytes) -> Dict[str, Any]:
        """Parse MDC protocol response"""
        if len(response) < 4:
            return {'success': False, 'error': 'Response too short'}
        
        try:
            header, cmd, display_id, data_length = struct.unpack('BBBB', response[:4])
            
            if header != 0xAA:
                return {'success': False, 'error': 'Invalid header'}
            
            if display_id != self.display_id:
                return {'success': False, 'error': 'Display ID mismatch'}
            
            data = response[4:4+data_length] if data_length > 0 else b''
            checksum = response[4+data_length] if len(response) > 4+data_length else 0
            
            # Verify checksum
            expected_checksum = (header + cmd + display_id + data_length + sum(data)) & 0xFF
            if checksum != expected_checksum:
                return {'success': False, 'error': 'Checksum mismatch'}
            
            return {
                'success': True,
                'command': cmd,
                'data': data,
                'raw_response': response
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Parse error: {str(e)}'}
    
    async def send_command(self, command: MDCCommand, data: bytes = b'', 
                          expect_response: bool = True) -> Dict[str, Any]:
        """Send command to display with enhanced error handling"""
        for attempt in range(self.max_retries):
            try:
                if not self.connected:
                    if not await self.connect():
                        continue
                
                packet = self._create_mdc_packet(command, data)
                
                # Send packet
                self.writer.write(packet)
                await self.writer.drain()
                
                if expect_response:
                    # Read response with timeout
                    try:
                        response = await asyncio.wait_for(
                            self.reader.read(1024), 
                            timeout=5.0
                        )
                        
                        if response:
                            self.last_response_time = time.time()
                            result = self._parse_mdc_response(response)
                            if result['success']:
                                return result
                            else:
                                logger.warning(f"Command failed: {result['error']}")
                        
                    except asyncio.TimeoutError:
                        logger.warning(f"Timeout waiting for response from display {self.display_id}")
                        self.connected = False
                        continue
                
                return {'success': True, 'message': 'Command sent successfully'}
                
            except Exception as e:
                logger.error(f"Command attempt {attempt + 1} failed: {e}")
                self.connected = False
                self.error_count += 1
                
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
        
        return {'success': False, 'error': f'Failed after {self.max_retries} attempts'}
    
    async def power_on(self) -> Dict[str, Any]:
        """Turn display power on"""
        return await self.send_command(MDCCommand.POWER, b'\x01')
    
    async def power_off(self) -> Dict[str, Any]:
        """Turn display power off"""
        return await self.send_command(MDCCommand.POWER, b'\x00')
    
    async def set_volume(self, volume: int) -> Dict[str, Any]:
        """Set display volume (0-100)"""
        if not 0 <= volume <= 100:
            return {'success': False, 'error': 'Volume must be between 0-100'}
        
        return await self.send_command(MDCCommand.VOLUME, bytes([volume]))
    
    async def set_mute(self, muted: bool) -> Dict[str, Any]:
        """Set mute state"""
        mute_value = 0x01 if muted else 0x00
        return await self.send_command(MDCCommand.MUTE, bytes([mute_value]))
    
    async def set_input_source(self, source: InputSource) -> Dict[str, Any]:
        """Set input source"""
        return await self.send_command(MDCCommand.INPUT_SOURCE, bytes([source.value]))
    
    async def get_temperature(self) -> Dict[str, Any]:
        """Get current display temperature"""
        result = await self.send_command(MDCCommand.CURRENT_TEMP, expect_response=True)
        if result['success'] and 'data' in result and len(result['data']) >= 1:
            temp = result['data'][0]
            result['temperature'] = temp
        return result
    
    async def get_serial_number(self) -> Dict[str, Any]:
        """Get display serial number"""
        result = await self.send_command(MDCCommand.SERIAL_NUMBER, expect_response=True)
        if result['success'] and 'data' in result:
            result['serial_number'] = result['data'].decode('ascii', errors='ignore').strip()
        return result
    
    async def get_model_number(self) -> Dict[str, Any]:
        """Get display model number"""
        result = await self.send_command(MDCCommand.MODEL_NUMBER, expect_response=True)
        if result['success'] and 'data' in result:
            result['model_number'] = result['data'].decode('ascii', errors='ignore').strip()
        return result
    
    async def get_software_version(self) -> Dict[str, Any]:
        """Get display software version"""
        result = await self.send_command(MDCCommand.SOFTWARE_VERSION, expect_response=True)
        if result['success'] and 'data' in result:
            result['software_version'] = result['data'].decode('ascii', errors='ignore').strip()
        return result
    
    async def set_video_wall_mode(self, enabled: bool, h_monitors: int = 1, 
                                 v_monitors: int = 1, h_position: int = 1, 
                                 v_position: int = 1) -> Dict[str, Any]:
        """Configure video wall mode"""
        if not 1 <= h_monitors <= 15 or not 1 <= v_monitors <= 15:
            return {'success': False, 'error': 'Monitor count must be 1-15'}
        
        if not 1 <= h_position <= h_monitors or not 1 <= v_position <= v_monitors:
            return {'success': False, 'error': 'Position must be within monitor grid'}
        
        wall_mode = 0x01 if enabled else 0x00
        data = struct.pack('BBBBB', wall_mode, h_monitors, v_monitors, h_position, v_position)
        
        return await self.send_command(MDCCommand.VIDEO_WALL_MODE, data)
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_data = {
            'display_id': self.display_id,
            'ip': self.ip,
            'connected': False,
            'responsive': False,
            'temperature': None,
            'error_count': self.error_count,
            'last_response': self.last_response_time,
            'model': None,
            'serial_number': None,
            'software_version': None
        }
        
        try:
            # Test connection
            if not self.connected:
                await self.connect()
            
            if self.connected:
                health_data['connected'] = True
                
                # Test responsiveness with temperature query
                temp_result = await self.get_temperature()
                if temp_result['success']:
                    health_data['responsive'] = True
                    health_data['temperature'] = temp_result.get('temperature')
                
                # Get device info (non-critical)
                try:
                    model_result = await self.get_model_number()
                    if model_result['success']:
                        health_data['model'] = model_result.get('model_number')
                    
                    serial_result = await self.get_serial_number()
                    if serial_result['success']:
                        health_data['serial_number'] = serial_result.get('serial_number')
                    
                    version_result = await self.get_software_version()
                    if version_result['success']:
                        health_data['software_version'] = version_result.get('software_version')
                        
                except Exception as e:
                    logger.debug(f"Non-critical info gathering failed: {e}")
        
        except Exception as e:
            logger.error(f"Health check failed for display {self.display_id}: {e}")
            health_data['error'] = str(e)
        
        return health_data


# Configuration Wizard Component
class VideoWallConfigWizard:
    """Interactive configuration wizard for video wall setup"""
    
    def __init__(self):
        self.config = {
            'displays': {},
            'magicinfo': {},
            'optisigns': {},
            'content': {},
            'server': {}
        }
    
    async def discover_displays(self, ip_range: str = "192.168.1.1-254") -> List[Dict]:
        """Discover Samsung displays on network"""
        discovered = []
        
        # Parse IP range
        if '-' in ip_range:
            base_ip, range_part = ip_range.rsplit('.', 1)
            start, end = map(int, range_part.split('-'))
        else:
            # Single IP
            return await self._test_single_ip(ip_range)
        
        # Test IP range
        tasks = []
        for i in range(start, end + 1):
            ip = f"{base_ip}.{i}"
            tasks.append(self._test_single_ip(ip))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict) and result.get('responsive'):
                discovered.append(result)
        
        return discovered
    
    async def _test_single_ip(self, ip: str) -> Optional[Dict]:
        """Test if IP has a responsive Samsung display"""
        try:
            adapter = SamsungLHB55ECHAdapter(1, ip)  # Use ID 1 for discovery
            health = await adapter.health_check()
            await adapter.disconnect()
            
            if health['responsive']:
                return {
                    'ip': ip,
                    'model': health.get('model', 'Samsung Display'),
                    'serial_number': health.get('serial_number'),
                    'temperature': health.get('temperature'),
                    'responsive': True
                }
        except Exception:
            pass
        
        return None
    
    def generate_config(self, discovered_displays: List[Dict], 
                       video_wall_layout: Tuple[int, int] = (2, 2)) -> Dict:
        """Generate configuration from discovered displays"""
        h_count, v_count = video_wall_layout
        
        config = {
            'displays': {},
            'video_wall': {
                'enabled': len(discovered_displays) > 1,
                'layout': {
                    'horizontal': h_count,
                    'vertical': v_count
                }
            },
            'magicinfo': {
                'enabled': False,
                'server_url': '',
                'username': 'admin',
                'password': '',
                'api_key': ''
            },
            'optisigns': {
                'enabled': False,
                'server_url': '',
                'api_key': '',
                'username': 'admin',
                'password': ''
            },
            'content': {
                'static_path': './static_content/',
                'upload_path': './uploads/',
                'max_file_size': 100,
                'allowed_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.mp4', '.avi', '.mov', '.webm']
            },
            'server': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            }
        }
        
        # Configure displays
        for i, display in enumerate(discovered_displays[:h_count * v_count], 1):
            # Calculate video wall position
            h_pos = ((i - 1) % h_count) + 1
            v_pos = ((i - 1) // h_count) + 1
            
            config['displays'][i] = {
                'name': f'Display {i} - {display.get("model", "Samsung")}',
                'ip': display['ip'],
                'port': 1515,
                'protocol': 'tcp',
                'model': 'LHB55ECH',
                'serial_number': display.get('serial_number', ''),
                'video_wall_position': {
                    'horizontal': h_pos,
                    'vertical': v_pos
                }
            }
        
        return config


# Enhanced Monitoring Dashboard Component
class MonitoringDashboard:
    """Real-time monitoring dashboard for video wall system"""
    
    def __init__(self, display_adapters: Dict[int, SamsungLHB55ECHAdapter]):
        self.adapters = display_adapters
        self.monitoring_active = False
        self.monitoring_interval = 30  # seconds
        self.alert_thresholds = {
            'temperature_warning': 70,  # Celsius
            'temperature_critical': 80,
            'response_timeout': 10,  # seconds
            'error_count_warning': 3
        }
        self.alerts = []
    
    async def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring_active = True
        while self.monitoring_active:
            await self._perform_health_checks()
            await asyncio.sleep(self.monitoring_interval)
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
    
    async def _perform_health_checks(self):
        """Perform health checks on all displays"""
        tasks = []
        for display_id, adapter in self.adapters.items():
            tasks.append(self._check_display_health(display_id, adapter))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results and generate alerts
        for result in results:
            if isinstance(result, dict):
                self._process_health_result(result)
    
    async def _check_display_health(self, display_id: int, 
                                   adapter: SamsungLHB55ECHAdapter) -> Dict:
        """Check health of individual display"""
        try:
            health_data = await adapter.health_check()
            health_data['timestamp'] = time.time()
            return health_data
        except Exception as e:
            return {
                'display_id': display_id,
                'error': str(e),
                'timestamp': time.time(),
                'connected': False,
                'responsive': False
            }
    
    def _process_health_result(self, health_data: Dict):
        """Process health check result and generate alerts"""
        display_id = health_data['display_id']
        current_time = time.time()
        
        # Check temperature
        if health_data.get('temperature'):
            temp = health_data['temperature']
            if temp >= self.alert_thresholds['temperature_critical']:
                self._add_alert('critical', f'Display {display_id} temperature critical: {temp}°C')
            elif temp >= self.alert_thresholds['temperature_warning']:
                self._add_alert('warning', f'Display {display_id} temperature high: {temp}°C')
        
        # Check connectivity
        if not health_data.get('connected'):
            self._add_alert('error', f'Display {display_id} not connected')
        elif not health_data.get('responsive'):
            self._add_alert('warning', f'Display {display_id} not responding')
        
        # Check response time
        if health_data.get('last_response'):
            response_age = current_time - health_data['last_response']
            if response_age > self.alert_thresholds['response_timeout']:
                self._add_alert('warning', f'Display {display_id} last response {response_age:.1f}s ago')
        
        # Check error count
        if health_data.get('error_count', 0) >= self.alert_thresholds['error_count_warning']:
            self._add_alert('warning', f'Display {display_id} has {health_data["error_count"]} errors')
    
    def _add_alert(self, level: str, message: str):
        """Add alert to the system"""
        alert = {
            'level': level,
            'message': message,
            'timestamp': time.time(),
            'id': f"{level}_{hash(message)}_{int(time.time())}"
        }
        
        # Avoid duplicate alerts (same message within 5 minutes)
        cutoff_time = time.time() - 300
        existing_alerts = [a for a in self.alerts if a['timestamp'] > cutoff_time and a['message'] == message]
        
        if not existing_alerts:
            self.alerts.append(alert)
            logger.warning(f"ALERT [{level.upper()}]: {message}")
            
            # Keep only last 100 alerts
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
    
    def get_current_alerts(self, level_filter: Optional[str] = None) -> List[Dict]:
        """Get current alerts, optionally filtered by level"""
        if level_filter:
            return [a for a in self.alerts if a['level'] == level_filter]
        return self.alerts.copy()
    
    def get_system_status(self) -> Dict:
        """Get overall system status"""
        total_displays = len(self.adapters)
        connected_displays = 0
        responsive_displays = 0
        avg_temperature = 0
        temp_count = 0
        
        recent_alerts = [a for a in self.alerts if time.time() - a['timestamp'] < 3600]  # Last hour
        
        for adapter in self.adapters.values():
            if hasattr(adapter, 'connected') and adapter.connected:
                connected_displays += 1
            
            # This would need to be stored from recent health checks
            # For now, we'll use placeholder logic
        
        return {
            'total_displays': total_displays,
            'connected_displays': connected_displays,
            'responsive_displays': responsive_displays,
            'connection_rate': connected_displays / total_displays if total_displays > 0 else 0,
            'recent_alerts': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a['level'] == 'critical']),
            'warning_alerts': len([a for a in recent_alerts if a['level'] == 'warning']),
            'system_health': 'healthy' if len(recent_alerts) == 0 else 'warning' if len([a for a in recent_alerts if a['level'] == 'critical']) == 0 else 'critical'
        }


# Video Wall Layout Manager
class VideoWallLayoutManager:
    """Manage video wall layouts and content distribution"""
    
    def __init__(self, displays: Dict[int, Dict]):
        self.displays = displays
        self.layouts = {}
        self._calculate_layouts()
    
    def _calculate_layouts(self):
        """Calculate possible video wall layouts"""
        display_count = len(self.displays)
        
        # Find all possible rectangular layouts
        for h in range(1, display_count + 1):
            if display_count % h == 0:
                v = display_count // h
                layout_name = f"{h}x{v}"
                self.layouts[layout_name] = {
                    'horizontal': h,
                    'vertical': v,
                    'total_displays': display_count,
                    'aspect_ratio': h / v,
                    'display_mapping': self._create_display_mapping(h, v)
                }
    
    def _create_display_mapping(self, h_count: int, v_count: int) -> Dict:
        """Create mapping of display positions"""
        mapping = {}
        display_ids = list(self.displays.keys())
        
        for i, display_id in enumerate(display_ids[:h_count * v_count]):
            h_pos = (i % h_count) + 1
            v_pos = (i // h_count) + 1
            
            mapping[display_id] = {
                'horizontal_position': h_pos,
                'vertical_position': v_pos,
                'grid_position': (h_pos, v_pos)
            }
        
        return mapping
    
    def get_available_layouts(self) -> Dict:
        """Get all available video wall layouts"""
        return self.layouts
    
    async def configure_video_wall(self, layout_name: str, 
                                  adapters: Dict[int, SamsungLHB55ECHAdapter]) -> Dict:
        """Configure displays for video wall mode"""
        if layout_name not in self.layouts:
            return {'success': False, 'error': 'Layout not found'}
        
        layout = self.layouts[layout_name]
        results = {}
        
        for display_id, position in layout['display_mapping'].items():
            if display_id in adapters:
                adapter = adapters[display_id]
                result = await adapter.set_video_wall_mode(
                    enabled=True,
                    h_monitors=layout['horizontal'],
                    v_monitors=layout['vertical'],
                    h_position=position['horizontal_position'],
                    v_position=position['vertical_position']
                )
                results[display_id] = result
            else:
                results[display_id] = {'success': False, 'error': 'Adapter not found'}
        
        return {
            'success': all(r.get('success', False) for r in results.values()),
            'layout': layout_name,
            'results': results
        }
    
    async def disable_video_wall(self, adapters: Dict[int, SamsungLHB55ECHAdapter]) -> Dict:
        """Disable video wall mode on all displays"""
        results = {}
        
        for display_id, adapter in adapters.items():
            result = await adapter.set_video_wall_mode(enabled=False)
            results[display_id] = result
        
        return {
            'success': all(r.get('success', False) for r in results.values()),
            'results': results
        }


# Usage Example and Integration
async def main():
    """Example usage of the Samsung LHB55ECH adapter and components"""
    
    # Initialize display adapters
    display_configs = {
        1: {'ip': '192.168.1.101'},
        2: {'ip': '192.168.1.102'},
        3: {'ip': '192.168.1.103'},
        4: {'ip': '192.168.1.104'}
    }
    
    adapters = {}
    for display_id, config in display_configs.items():
        adapters[display_id] = SamsungLHB55ECHAdapter(display_id, config['ip'])
    
    # Configuration Wizard Example
    print("Starting configuration wizard...")
    wizard = VideoWallConfigWizard()
    discovered = await wizard.discover_displays("192.168.1.100-110")
    print(f"Discovered {len(discovered)} displays")
    
    if discovered:
        config = wizard.generate_config(discovered, (2, 2))
        print("Generated configuration:", config)
    
    # Video Wall Layout Example
    layout_manager = VideoWallLayoutManager(display_configs)
    layouts = layout_manager.get_available_layouts()
    print("Available layouts:", list(layouts.keys()))
    
    # Configure 2x2 video wall
    if '2x2' in layouts:
        result = await layout_manager.configure_video_wall('2x2', adapters)
        print("Video wall configuration result:", result)
    
    # Monitoring Example
    monitor = MonitoringDashboard(adapters)
    
    # Start monitoring in background
    monitoring_task = asyncio.create_task(monitor.start_monitoring())
    
    # Wait a bit to collect some data
    await asyncio.sleep(5)
    
    # Get system status
    status = monitor.get_system_status()
    print("System status:", status)
    
    # Get current alerts
    alerts = monitor.get_current_alerts()
    print(f"Current alerts: {len(alerts)}")
    
    # Stop monitoring
    monitor.stop_monitoring()
    await monitoring_task
    
    # Cleanup
    for adapter in adapters.values():
        await adapter.disconnect()

if __name__ == "__main__":
    asyncio.run(main())