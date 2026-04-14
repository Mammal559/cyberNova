# Data Analytics Dashboard - Project Specification

## Overview
A high-performance Python-based Data Analytics Dashboard that automatically maps geography, ingests raw IIS log files, and produces interactive statistical reports showing system performance metrics and sales lead conversions.

## Technology Stack
- **Backend**: Python
- **Frontend**: Streamlit
- **Styling**: Tailwind CSS
- **Database**: PostgreSQL (recommended) / SQLite (file-based)
- **Authentication**: Argon2/bcrypt password hashing
- **Security**: HTTPS/TLS 1.2+

---

## File-Based Architecture (School Project Option)

### Overview
For school projects where external backend hosting is not feasible, this architecture uses file-based storage with Streamlit as the complete solution, eliminating the need for separate database servers.

### File Storage System
```
data/
├── users.json              # User accounts and roles
├── sessions/               # Active session files
├── logs.db                 # SQLite database for IIS logs
├── analytics_cache/        # Cached analysis results
├── reports/                # Generated reports
├── audit_logs/             # User activity logs
├── config/                 # Configuration files
└── geoip/                  # Local GeoIP database
```

### Technology Adaptations
- **Database**: SQLite (embedded, self-contained)
- **User Management**: JSON files with bcrypt hashing
- **Sessions**: Streamlit session_state + file persistence
- **API Layer**: Python functions within Streamlit
- **Caching**: File-based pickle storage
- **Authentication**: File-based user validation

### Benefits for School Projects
- **No External Hosting**: Everything runs in Streamlit Cloud
- **Self-Contained**: Data travels with the application
- **Easy Deployment**: Single file upload to Streamlit
- **Zero Maintenance**: No database server management
- **Cost-Free**: No hosting or database costs
- **Portable**: Easy to share and demonstrate

### Implementation Changes
- Replace PostgreSQL with SQLite for log data
- Use JSON files instead of database tables for users
- Implement file-based CRUD operations
- Create API-like functions within Streamlit pages
- Use Streamlit secrets for sensitive configuration
- File-based audit logging instead of database logs

---

## Phase 1: Data Ingestion and Security

### Functional Requirements

#### FR-1: IIS Log Processing
- Extract from W3C format IIS logs:
  - Timestamp
  - IP address
  - URL
  - HTTP status
  - Bytes transferred
- Support batch processing of large log files
- Automated log parsing and validation

#### FR-2: User Authentication
- Secure login with username and password
- Password encryption using Argon2 or bcrypt
- Configurable session timeout
- Multi-factor authentication support (optional)

### Non-Functional Requirements

#### NFR-1: Security
- Salt-based password hashing
- HTTPS/TLS 1.2+ encryption
- Protection against:
  - SQL injection
  - Cross-site scripting (XSS)
  - Cross-site request forgery (CSRF)
- Input validation and sanitization

#### NFR-2: Data Privacy
- GDPR compliance
- Data anonymization capabilities
- Configurable data retention policies
- Right to be forgotten implementation

#### NFR-3: Performance
- Fast analysis of large log datasets
- Dashboard loading under 3 seconds
- Report generation within minutes
- Support for millions of log entries

#### NFR-4: Data Integrity
- Referential integrity constraints
- Input validation at all entry points
- Transaction rollbacks during log ingestion
- Data consistency checks

---

## Phase 2: Interactive Visualization and Analytics

### Functional Requirements

#### FR-3: Geographic Analysis
- IP address to geographical location mapping
- Interactive world/regional maps
- Visitor distribution visualization
- Heat maps for traffic density
- Country/city-level analytics

#### FR-4: Traffic Pattern Analysis
- Peak traffic time identification
- Visit frequency analysis
- Time-based trend analysis:
  - Hourly patterns
  - Daily patterns
  - Weekly patterns
  - Monthly patterns
- Seasonal trend detection

#### FR-5: Dashboard Visualization
- Interactive chart types:
  - Bar charts
  - Pie charts
  - Line charts
  - Scatter plots
  - Heat maps
- Export capabilities:
  - PNG
  - PDF
  - SVG
- Real-time data refresh

### Non-Functional Requirements

#### NFR-5: Browser Support
- Chrome (latest 2 versions)
- Firefox (latest 2 versions)
- Edge (latest 2 versions)
- Safari (latest 2 versions)
- Responsive design for mobile/tablet

#### NFR-6: Usability
- Intuitive user interface
- Minimal training requirement
- Clear error messages
- Comprehensive help documentation
- Cost-effective support model

---

## Phase 3: Advanced Accountability and Reporting

### Functional Requirements

#### FR-6: Report Generation
- Automated scheduled reports
- Multiple export formats:
  - PDF
  - Excel
  - CSV
- Customizable report templates
- Email delivery integration

#### FR-7: Data Filtering
- Advanced search capabilities
- Filter by:
  - IP address ranges
  - Service type
  - Geographic location
  - Date ranges
  - HTTP status codes
- Saved filter configurations

#### FR-8: Role-Based Access Control
- **Administrator**: Complete system access
- **Analyst**: Reports and analysis tools
- **Viewer**: Read-only dashboard access
- Granular permission settings

#### FR-9: Audit Logging
- Comprehensive user action logging:
  - Login attempts
  - Data access
  - Report generation
  - Configuration changes
- Immutable audit trail
- Compliance reporting

### Non-Functional Requirements

#### NFR-7: Maintainability
- Modular architecture
- Well-documented code
- Version-controlled database migrations
- Automated testing suite
- Code quality standards

---

## Future Phases

### Additional Features

#### Dashboard Customization
- User-customizable dashboard layouts
- Personal widget arrangements
- Custom chart configurations
- Saved dashboard templates

#### Scalability
- Support for 50+ concurrent users
- 500% increase in data volume capacity
- Horizontal scaling capabilities
- Load balancing implementation

#### Monitoring and Alerts
- Real-time system monitoring
- Automated anomaly detection
- Traffic threshold alerts
- Performance metric monitoring
- Notification system integration

---

## Technical Architecture

### Backend Components
```
├── Data Ingestion Layer
│   ├── IIS Log Parser
│   ├── Data Validator
│   └── Database Loader
├── Analytics Engine
│   ├── Geographic Mapping
│   ├── Traffic Analysis
│   └── Statistical Processing
├── Security Layer
│   ├── Authentication
│   ├── Authorization
│   └── Audit Logging
└── API Layer
    ├── RESTful Endpoints
    └── WebSocket Support
```

### Frontend Components
```
├── Streamlit Application
├── Dashboard Components
│   ├── Charts & Graphs
│   ├── Maps
│   └── Filters
├── User Management
└── Report Generation
```

### Database Schema
```sql
-- Core tables
users
user_sessions
audit_logs
iis_logs
geographic_data
reports
user_permissions

-- Analytics tables
traffic_patterns
geographic_stats
performance_metrics
system_alerts
```

---

## Development Roadmap

### Phase 1 (Weeks 1-4)
- [ ] Set up development environment
- [ ] Implement IIS log parser
- [ ] Create user authentication system
- [ ] Design database schema
- [ ] Implement basic security measures

### Phase 2 (Weeks 5-8)
- [ ] Build Streamlit dashboard
- [ ] Integrate geographic mapping
- [ ] Implement traffic analysis
- [ ] Create interactive visualizations
- [ ] Add export functionality

### Phase 3 (Weeks 9-12)
- [ ] Implement role-based access control
- [ ] Add audit logging
- [ ] Create report generation system
- [ ] Implement advanced filtering
- [ ] Performance optimization

### Future Phases (Weeks 13+)
- [ ] Dashboard customization
- [ ] Scalability improvements
- [ ] Real-time monitoring
- [ ] Advanced alerting system

---

## Security Considerations

### Data Protection
- Encryption at rest and in transit
- Regular security audits
- Penetration testing
- Vulnerability scanning

### Compliance
- GDPR implementation
- Data retention policies
- Right to erasure
- Privacy by design

---

## Performance Targets

### Response Times
- Dashboard load: < 3 seconds
- Report generation: < 2 minutes
- Search queries: < 1 second
- Data ingestion: 10,000 records/second

### Scalability Metrics
- Concurrent users: 50+
- Data volume: 500% growth capacity
- Uptime: 99.9%
- Backup recovery: < 4 hours

---

## Testing Strategy

### Unit Testing
- Log parsing accuracy
- Authentication flows
- Data validation
- Business logic

### Integration Testing
- Database operations
- API endpoints
- Third-party integrations
- Security controls

### Performance Testing
- Load testing
- Stress testing
- Volume testing
- Endurance testing

---

## Deployment Architecture

### Production Environment
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │────│   Web Server    │────│   Database      │
│   (Nginx)       │    │   (Streamlit)   │    │   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   File Storage  │
                    │   (Logs/Reports)│
                    └─────────────────┘
```

### Monitoring and Observability
- Application performance monitoring
- Database performance metrics
- User behavior analytics
- System health checks

---

## Project Success Criteria

### Functional Success
- All requirements implemented and tested
- User acceptance testing passed
- Performance targets met
- Security audit passed

### Business Success
- Improved data visibility
- Enhanced decision-making
- Reduced manual reporting effort
- Compliance with regulations

---

*Last Updated: April 2026*
*Version: 1.0*
