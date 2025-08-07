# War
Media Wall Dashboard/Control Hub
# README.md
# Video Wall Control Panel

A comprehensive control system for managing video wall displays with support for Samsung MagicInfo, OptiSigns, and custom content deployment.

## Features

- **Display Control**: Power, volume, input source management
- **Content Management**: Static content, streaming, scheduled deployment
- **Multi-Platform Support**: MagicInfo, OptiSigns integration
- **Real-Time Monitoring**: WebSocket-based status updates
- **Scheduling**: Automated content deployment
- **Web Interface**: Tablet-optimized control panel

## Quick Start

### Requirements

- Python 3.8+
- Network access to displays
- Optional: MagicInfo Server, OptiSigns account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/video-wall-control.git
cd video-wall-control
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your system:
```bash
cp config.yaml.example config.yaml
# Edit config.yaml with your display IPs and credentials
```

4. Run the server:
```bash
python video_wall_server.py
```

5. Open the control panel:
```
http://localhost:5000
```

### Docker Deployment

```bash
docker-compose up -d
```

## Configuration

### Display Setup

Update `config.yaml` with your display information:

```yaml
displays:
  1:
    name: "Main Display"
    ip: "192.168.1.101"
    port: 1515
    protocol: "tcp"
```

### MagicInfo Integration

```yaml
magicinfo:
  server_url: "http://your-magicinfo-server:7001"
  username: "admin"
  password: "your-password"
  api_key: "your-api-key"
```

### OptiSigns Integration

```yaml
optisigns:
  server_url: "http://your-optisigns-server:8080"
  api_key: "your-api-key"
```

## API Documentation

### Display Control

- `POST /api/displays/{id}/power` - Control display power
- `POST /api/displays/{id}/volume` - Set volume level
- `POST /api/displays/{id}/input` - Change input source
- `GET /api/displays/{id}/status` - Get display status

### Content Management

- `POST /api/content/deploy` - Deploy content to displays
- `POST /api/content/schedule` - Schedule content deployment
- `GET /api/magicinfo/channels` - Get MagicInfo channels
- `GET /api/optisigns/playlists` - Get OptiSigns playlists

## Supported Display Protocols

- **Samsung MDC Protocol** (TCP/IP)
- **RS232 Serial** (COM ports)
- **Custom HTTP APIs**

## Production Deployment

### Using systemd

```bash
sudo ./install.sh
```

### Using Docker

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### SSL Configuration

Update nginx configuration for HTTPS:

```nginx
server {
    listen 443 ssl;
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    # ... rest of config
}
```

## Troubleshooting

### Common Issues

1. **Display not responding**: Check network connectivity and port configuration
2. **MagicInfo integration fails**: Verify server URL and credentials
3. **Content not deploying**: Check file permissions and paths

### Logs

```bash
tail -f /opt/video-wall-control/logs/video_wall.log
```

### Debug Mode

```bash
FLASK_ENV=development python video_wall_server.py
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- Documentation: [Wiki](https://github.com/yourusername/video-wall-control/wiki)
- Issues: [GitHub Issues](https://github.com/yourusername/video-wall-control/issues)
- Email: support@yourcompany.com
