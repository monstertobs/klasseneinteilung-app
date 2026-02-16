# Version History - Klasseneinteilung App

**Author:** Tobias Meier <admin(at)secutobs.com>
**Project:** Klasseneinteilung App - Intelligente Klasseneinteilung für 5. Klassen
**Repository:** klasseneinteilung-app

---

## Version 2.0.0 - Feature Extension Release
**Release Date:** February 13, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable

### 🎉 Major Features Added

This release adds 6 major features to enhance the class assignment system with advanced options, interactive preview, and conflict resolution.

#### **1. Export Function (Excel, CSV, PDF)**
- Multi-format export for class lists
- Excel: Multi-sheet workbook with statistics
- CSV: Semicolon-delimited, UTF-8 encoded
- PDF: Professional layout with ReportLab
- **Files:** `app.py` (+200 lines), `generate.html` (+30 lines)
- **Dependencies:** Added `reportlab==4.0.9`

#### **2. Multiple Specialized Classes**
- Support for Sport, Musik, and Theater classes
- Student interest tracking with checkboxes
- Algorithm prioritizes students for matching classes
- Visual badges (⚽🎵🎭) on class headers
- **Database:** Added columns `sport_interesse`, `musik_interesse`, `theater_interesse`
- **Files:** `app.py` (+150 lines), `add_student.html`, `edit_student.html`, `generate.html`

#### **3. Religion Bundling**
- Prevents pure Ethik-only classes
- Promotes religious diversity
- Intelligent scoring for mixed religion classes
- **Files:** `app.py` (+30 lines), `generate.html` (+10 lines)

#### **4. IB Min/Max Constraints**
- Configurable minimum and maximum IB students per class
- Pre-generation validation and warnings
- Classes have either 0 or between min-max IB students
- **Files:** `app.py` (+50 lines), `generate.html` (+20 lines)

#### **5. Drag & Drop Student Movements**
- Interactive preview mode for class adjustments
- Visual feedback with grab cursor and animations
- Real-time statistics updates
- Modification tracking without database changes
- **New File:** `static/js/drag-drop.js` (433 lines)
- **Files Modified:** `generate.html` (+40 lines), `style.css` (+80 lines)

#### **6. Conflict Detection & Resolution**
- Automatic conflict detection when moving students
- Modal dialog with severity levels
- Solution suggestions with scoring
- Three action options: Revert, Accept, or View Suggestions
- **New Routes:** `/check_conflicts`, `/suggest_swaps`
- **Files:** `app.py` (+120 lines), `drag-drop.js`, `style.css` (+70 lines)

### 🔧 Technical Improvements

- **Password Hashing:** Switched from scrypt to pbkdf2:sha256 for better compatibility
- **Error Handling:** Improved error handling in init_db()
- **Code Quality:** 1,200+ lines of well-documented code added
- **Performance:** Optimized DOM manipulation in drag & drop
- **Security:** CSRF protection on all AJAX calls

### 📊 Statistics

- **Files Created:** 2 (drag-drop.js, VERSION_HISTORY.md)
- **Files Modified:** 7
- **Lines Added:** ~1,200
- **New Routes:** 3
- **New Database Columns:** 3
- **Dependencies Added:** 1 (reportlab)

### 🐛 Bug Fixes

- Fixed scrypt unavailability on some Python installations
- Improved session handling for drag & drop state
- Fixed sorting of students after drag & drop operations

### 📝 Documentation

- Added `IMPLEMENTATION_SUMMARY.md`
- Added `VERSION_HISTORY.md`
- Updated inline code documentation
- Added comprehensive testing documentation

---

## Version 1.0.0 - Initial Release
**Release Date:** January 30, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ✅ Stable (Superseded by v2.0.0)

### 🎯 Core Features

#### **Class Generation Algorithm**
- Intelligent distribution of students across classes (~25 students per class)
- Multi-factor scoring system
- Three proposal variants with different random seeds

#### **Scoring Priorities**
1. **Gender Balance** (Highest Priority)
   - Target: 50/50 distribution
   - Score penalty: -15 per gender ratio deviation
2. **School Route Grouping**
   - Groups students from same area (Wohnort)
   - Enables carpooling
   - Score bonus: +12 per matching location
3. **Friend Wishes**
   - Together wishes: +20 bonus
   - Separation wishes: -20 penalty
4. **School Type Distribution** (Schulform)
   - Balanced distribution of H/R/G/IB
   - Score penalty: -8 per ratio deviation
5. **Religion Distribution** (Secondary)
   - Optional distribution or grouping
   - Score impact: ±2 points

#### **Student Management**
- Add, edit, delete students
- Import from CSV/Excel
- Duplicate detection
- Fields: Name, Gender, Wohnort, Schulform, Religion, Special Needs, Notes

#### **Parent Wishes Management**
- Together wishes (students want to be in same class)
- Separation wishes (students should be in different classes)
- Automatic import from CSV/Excel

#### **Security Features**
- CSRF Protection (Flask-WTF)
- Rate Limiting (Flask-Limiter: 10 login attempts/minute)
- Session Security (HttpOnly, SameSite, Secure cookies)
- Strong Password Requirements (8+ chars, upper, lower, digit)
- Custom Error Handlers (404, 500, 429)

#### **User Management**
- Multi-user support (max 10 users)
- Role-based access (login required)
- Password strength validation
- Session timeout (2 hours)

#### **Database Schema**
- SQLite database
- Tables: users, students, parent_wishes, class_assignments
- Automatic migrations on startup

#### **UI/UX**
- Apple-inspired design system
- Responsive layout
- German language UI
- Print-friendly views
- Flash message system

### 📊 Statistics

- **Files Created:** 23
- **Lines of Code:** ~1,330 (app.py)
- **Templates:** 16 (Jinja2)
- **Routes:** 18 endpoints
- **Database Tables:** 4

---

## Version 0.5.0 - Beta Release
**Release Date:** January 15, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ⚠️ Beta (Superseded)

### Features

- Basic class generation algorithm
- Student CRUD operations
- CSV import functionality
- Simple login system
- Basic dashboard

### Known Issues

- No parent wishes support
- Limited import flexibility
- No security features
- Single user only

---

## Version 0.1.0 - Alpha Release
**Release Date:** January 1, 2026
**Author:** Tobias Meier <admin(at)secutobs.com>
**Status:** ⚠️ Alpha (Superseded)

### Features

- Proof of concept
- Random class distribution
- Basic student list
- No database persistence

---

## Roadmap

### Version 2.1.0 (Planned)
- [ ] Advanced conflict resolution strategies
- [ ] Class balancing optimizer
- [ ] Batch import improvements
- [ ] Export customization options
- [ ] Performance optimizations for large datasets

### Version 2.2.0 (Planned)
- [ ] Teacher assignment integration
- [ ] Room allocation
- [ ] Timetable integration
- [ ] Advanced reporting
- [ ] Multi-language support

### Version 3.0.0 (Future)
- [ ] API for external integrations
- [ ] Real-time collaboration
- [ ] Advanced analytics
- [ ] Machine learning optimization
- [ ] Mobile app

---

## Upgrade Guide

### From v1.0.0 to v2.0.0

**Database Migration:**
- Automatic migration runs on startup
- New columns added: `sport_interesse`, `musik_interesse`, `theater_interesse`
- No manual intervention required
- Existing data preserved

**Dependencies:**
```bash
pip install -r requirements.txt  # Installs reportlab==4.0.9
```

**Configuration:**
- No configuration changes required
- All new features are optional
- Backward compatible with v1.0 usage

**Breaking Changes:**
- None - fully backward compatible

---

## Support & Contact

**Author:** Tobias Meier
**Email:** admin(at)secutobs.com
**Project:** Klasseneinteilung App

For issues, questions, or feature requests, please contact the author.

---

## License

**Copyright © 2026 Tobias Meier**
All rights reserved.

This software is proprietary and confidential. Unauthorized copying, distribution, or use is strictly prohibited.

---

**Last Updated:** February 13, 2026
**Current Version:** 2.0.0
**Maintained By:** Tobias Meier <admin(at)secutobs.com>
