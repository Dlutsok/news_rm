# Changelog

All notable changes to Medical News Automation System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Removed - 2025-10-07
- **System Monitoring Feature** - Removed complete system monitoring functionality
  - Removed `backend/api/monitoring.py` - 10 API endpoints for system metrics
  - Removed `backend/services/system_monitoring.py` - System metrics collection service
  - Removed `frontend/pages/system-monitoring.js` - System monitoring UI page
  - Removed `frontend/components/monitoring/` directory with 4 components:
    - SystemMonitoringDashboard.js
    - ServiceStatusCard.js
    - SystemMetricsPanel.js
    - AlertsPanel.js
  - Removed "Мониторинг системы" menu item from Navigation
  - Updated `backend/main.py` - removed monitoring router registration

### Preserved
- ✅ `backend/services/db_monitoring.py` - Database monitoring service (used by admin API)
- ✅ `frontend/pages/monitoring.js` - News monitoring page (main dashboard)
- ✅ Admin DB statistics endpoints (`/api/admin/stats/database/*`)

### Technical Details
- Total lines removed: ~1600 lines of code
- Endpoints removed: `/api/admin/monitoring/*` (10 endpoints)
- Dependencies preserved: `aiohttp` (used by news parsers), `psutil` (may be removed later)
- Zero breaking changes to news monitoring or admin DB stats functionality

### Migration Notes
- No database migrations required
- No configuration changes needed
- System monitoring page will return 404 (expected)
- All other functionality remains intact

---

## [1.0.0] - 2025-09-22
- Initial production release
- Full-stack medical news aggregation platform
- AI-powered content generation
- Multi-project support (GS, PS, TS)
- Automated publishing to Bitrix CMS and Telegram
