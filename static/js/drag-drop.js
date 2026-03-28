/**
 * Drag & Drop functionality for student movements
 * Allows preview mode changes without saving to database
 */

// State Management
let proposalModifications = {};
let draggedStudent = null;
let originalClass = null;
let pendingMove = null;

/**
 * Initialize drag and drop on all student items
 */
function initializeDragDrop() {
    const studentItems = document.querySelectorAll('.student-item[draggable="true"]');
    studentItems.forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
    });

    const classCards = document.querySelectorAll('.class-card');
    classCards.forEach(card => {
        card.addEventListener('dragover', handleDragOver);
        card.addEventListener('drop', handleDrop);
        card.addEventListener('dragleave', handleDragLeave);
    });
}

/**
 * Handle drag start event
 */
function handleDragStart(event) {
    const studentItem = event.currentTarget;
    const classCard = studentItem.closest('.class-card');

    draggedStudent = {
        id: studentItem.dataset.studentId,
        name: studentItem.dataset.studentName,
        element: studentItem,
        sourceClass: classCard.dataset.classId,
        sourceClassName: classCard.dataset.className
    };

    originalClass = classCard;

    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/html', studentItem.innerHTML);

    studentItem.style.opacity = '0.4';
    studentItem.classList.add('dragging');
}

/**
 * Handle drag end event
 */
function handleDragEnd(event) {
    event.currentTarget.style.opacity = '1';
    event.currentTarget.classList.remove('dragging');
    document.querySelectorAll('.class-card').forEach(card => {
        card.classList.remove('drag-over');
    });
}

/**
 * Handle drag over event
 */
function handleDragOver(event) {
    if (event.preventDefault) event.preventDefault();
    const classCard = event.currentTarget;
    if (draggedStudent && classCard.dataset.classId !== draggedStudent.sourceClass) {
        event.dataTransfer.dropEffect = 'move';
        classCard.classList.add('drag-over');
    } else {
        event.dataTransfer.dropEffect = 'none';
    }
    return false;
}

/**
 * Handle drag leave event
 */
function handleDragLeave(event) {
    event.currentTarget.classList.remove('drag-over');
}

/**
 * Handle drop event — shows conflict preview BEFORE moving
 */
function handleDrop(event) {
    if (event.stopPropagation) event.stopPropagation();
    event.preventDefault();

    const targetClassCard = event.currentTarget;
    const targetClass = targetClassCard.dataset.classId;
    const targetClassName = targetClassCard.dataset.className;

    targetClassCard.classList.remove('drag-over');

    if (!draggedStudent || targetClass === draggedStudent.sourceClass) return false;

    // Store pending move — execute only after user confirms in modal
    pendingMove = {
        student: draggedStudent,
        targetClassCard: targetClassCard,
        targetClass: targetClass,
        targetClassName: targetClassName
    };

    // Build current class state from DOM
    const currentState = buildCurrentState();

    // Compute client-side impact (sizes, gender)
    const impact = computeMoveImpact(draggedStudent, targetClass);

    // Get conflicts from server, then show modal
    fetchConflicts(draggedStudent.id, draggedStudent.sourceClass, targetClass, currentState, function(conflicts) {
        showPreMoveModal(conflicts, impact);
    });

    return false;
}

/**
 * Build a map of student_id -> class_id from the current DOM
 */
function buildCurrentState() {
    const state = {};
    document.querySelectorAll('.student-item[data-student-id]').forEach(item => {
        const card = item.closest('.class-card');
        if (card) state[item.dataset.studentId] = card.dataset.classId;
    });
    return state;
}

/**
 * Compute class stats (size, gender) before and after the move
 */
function computeMoveImpact(student, targetClass) {
    const studentEl = document.querySelector(`.student-item[data-student-id="${student.id}"]`);
    const gender = studentEl ? studentEl.dataset.gender : null;
    const isIB = studentEl ? studentEl.dataset.schulform === 'IB' : false;

    function getStats(classId) {
        const card = document.querySelector(`.class-card[data-class-id="${classId}"]`);
        if (!card) return { total: 0, m: 0, w: 0, ib: 0, name: classId };
        const items = card.querySelectorAll('.student-list .student-item');
        let m = 0, w = 0, ib = 0;
        items.forEach(s => {
            if (s.dataset.gender === 'm') m++;
            else if (s.dataset.gender === 'w') w++;
            if (s.dataset.schulform === 'IB') ib++;
        });
        return { total: items.length, m, w, ib, name: card.dataset.className || classId };
    }

    const src = getStats(student.sourceClass);
    const tgt = getStats(targetClass);

    const gDelta = gender === 'm' ? { m: -1, w: 0 } : (gender === 'w' ? { m: 0, w: -1 } : { m: 0, w: 0 });
    const ibDelta = isIB ? -1 : 0;

    return {
        studentName: student.name,
        gender: gender,
        isIB: isIB,
        source: {
            name: src.name,
            before: src,
            after: { total: src.total - 1, m: src.m + gDelta.m, w: src.w + gDelta.w, ib: src.ib + ibDelta }
        },
        target: {
            name: tgt.name,
            before: tgt,
            after: { total: tgt.total + 1, m: tgt.m - gDelta.m, w: tgt.w - gDelta.w, ib: tgt.ib - ibDelta }
        }
    };
}

/**
 * Fetch conflicts from server
 */
function fetchConflicts(studentId, sourceClass, targetClass, currentState, callback) {
    const csrfToken = document.querySelector('[name="csrf_token"]').value;
    fetch('/check_conflicts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken },
        body: JSON.stringify({
            student_id: studentId,
            source_class: sourceClass,
            target_class: targetClass,
            current_state: currentState,
            modifications: proposalModifications
        })
    })
    .then(r => r.json())
    .then(data => callback(data.conflicts || []))
    .catch(() => callback([]));
}

/**
 * Show the pre-move conflict preview modal
 */
function showPreMoveModal(conflicts, impact) {
    // Remove any existing modal
    closeMoveModal();

    const hasConflicts = conflicts.length > 0;
    const src = impact.source;
    const tgt = impact.target;

    // --- Impact section ---
    let impactHTML = `
        <div class="premove-impact">
            <div class="premove-impact-row">
                <span class="premove-class-name">${escapeHtml(src.name)}</span>
                <span class="premove-arrow">→</span>
                <span>${src.before.total} <span class="premove-dim">Schüler</span></span>
                <span class="premove-arrow">→</span>
                <span class="${src.after.total !== src.before.total ? 'premove-changed' : ''}">${src.after.total} <span class="premove-dim">Schüler</span></span>
                <span class="premove-gender">M ${src.before.m} / W ${src.before.w} → M ${src.after.m} / W ${src.after.w}</span>
            </div>
            <div class="premove-impact-row">
                <span class="premove-class-name">${escapeHtml(tgt.name)}</span>
                <span class="premove-arrow">→</span>
                <span>${tgt.before.total} <span class="premove-dim">Schüler</span></span>
                <span class="premove-arrow">→</span>
                <span class="${tgt.after.total !== tgt.before.total ? 'premove-changed' : ''}">${tgt.after.total} <span class="premove-dim">Schüler</span></span>
                <span class="premove-gender">M ${tgt.before.m} / W ${tgt.before.w} → M ${tgt.after.m} / W ${tgt.after.w}</span>
            </div>
        </div>`;

    // --- Conflicts section ---
    let conflictsHTML = '';
    if (hasConflicts) {
        conflictsHTML = '<div class="premove-section-title premove-section-warn">⚠️ Konflikte</div><ul class="conflict-list">';
        conflicts.forEach(c => {
            const cls = c.severity === 'critical' ? 'conflict-critical' : (c.severity === 'high' ? 'conflict-high' : 'conflict-medium');
            conflictsHTML += `<li class="conflict-item ${cls}">${escapeHtml(c.message)}</li>`;
        });
        conflictsHTML += '</ul>';
    } else {
        conflictsHTML = '<div class="premove-no-conflict">✅ Keine Elternwunsch-Konflikte erkannt</div>';
    }

    // --- Buttons ---
    const moveLabel = hasConflicts ? 'Trotzdem verschieben' : 'Verschieben';
    const moveBtnClass = hasConflicts ? 'btn btn-danger' : 'btn btn-primary';

    const html = `
        <div class="premove-header">
            <span class="premove-icon">🔄</span>
            <div>
                <div class="premove-title">Schüler verschieben</div>
                <div class="premove-subtitle">${escapeHtml(impact.studentName)}</div>
            </div>
        </div>
        <div class="premove-route">${escapeHtml(src.name)} &rarr; ${escapeHtml(tgt.name)}</div>
        <div class="premove-section-title">Auswirkungen auf Klassen</div>
        ${impactHTML}
        ${conflictsHTML}
        <div class="conflict-actions">
            <button class="btn btn-secondary" onclick="cancelPendingMove()">Abbrechen</button>
            <button class="${moveBtnClass}" onclick="confirmPendingMove()">${moveLabel}</button>
        </div>`;

    const overlay = document.createElement('div');
    overlay.className = 'conflict-overlay';
    overlay.id = 'premove-overlay';
    overlay.onclick = cancelPendingMove;

    const dialog = document.createElement('div');
    dialog.className = 'conflict-dialog';
    dialog.id = 'premove-dialog';
    dialog.innerHTML = html;
    dialog.onclick = e => e.stopPropagation();

    document.body.appendChild(overlay);
    document.body.appendChild(dialog);
}

/**
 * Close the pre-move modal without moving
 */
function cancelPendingMove() {
    closeMoveModal();
    // Restore opacity of dragged student
    if (pendingMove && pendingMove.student && pendingMove.student.element) {
        pendingMove.student.element.style.opacity = '1';
    }
    pendingMove = null;
    draggedStudent = null;
}

/**
 * Confirm and execute the pending move
 */
function confirmPendingMove() {
    closeMoveModal();
    if (!pendingMove) return;
    const { student, targetClassCard, targetClass } = pendingMove;

    moveStudentElement(student, targetClassCard);
    updateClassCounts(student.sourceClass, targetClass, student.id);

    proposalModifications[student.id] = {
        from: student.sourceClass,
        to: targetClass,
        studentName: student.name
    };

    showModificationIndicator();
    pendingMove = null;
    draggedStudent = null;
}

/**
 * Remove the modal and overlay from DOM
 */
function closeMoveModal() {
    const d = document.getElementById('premove-dialog');
    const o = document.getElementById('premove-overlay');
    if (d) d.remove();
    if (o) o.remove();
    // Also remove old-style conflict dialog if present
    const cd = document.getElementById('conflict-dialog');
    const co = document.querySelector('.conflict-overlay:not(#premove-overlay)');
    if (cd) cd.remove();
    if (co) co.remove();
}

/**
 * Move student element to target class
 */
function moveStudentElement(student, targetClassCard) {
    const studentList = targetClassCard.querySelector('.student-list');
    if (!studentList) return;

    student.element.remove();

    const students = Array.from(studentList.querySelectorAll('.student-item'));
    const studentName = student.name;

    let inserted = false;
    for (let i = 0; i < students.length; i++) {
        if (studentName.localeCompare(students[i].dataset.studentName, 'de') < 0) {
            studentList.insertBefore(student.element, students[i]);
            inserted = true;
            break;
        }
    }
    if (!inserted) studentList.appendChild(student.element);

    student.element.style.opacity = '1';
    student.element.style.backgroundColor = 'rgba(0, 122, 255, 0.1)';
    setTimeout(() => { student.element.style.backgroundColor = ''; }, 500);
}

/**
 * Update class statistics after move
 */
function updateClassCounts(sourceClassId, targetClassId, studentId) {
    const studentElement = document.querySelector(`[data-student-id="${studentId}"]`);
    if (!studentElement) return;

    const gender = studentElement.dataset.gender || 'm';
    const hasSpecialNeeds = studentElement.dataset.specialNeeds === 'true';
    const isIB = studentElement.dataset.schulform === 'IB';

    const sourceCard = document.querySelector(`.class-card[data-class-id="${sourceClassId}"]`);
    if (sourceCard) updateSingleClassCount(sourceCard, gender, hasSpecialNeeds, isIB, -1);

    const targetCard = document.querySelector(`.class-card[data-class-id="${targetClassId}"]`);
    if (targetCard) updateSingleClassCount(targetCard, gender, hasSpecialNeeds, isIB, 1);
}

/**
 * Update counts for a single class
 */
function updateSingleClassCount(classCard, gender, hasSpecialNeeds, isIB, delta) {
    const countBadge = classCard.querySelector('.class-count');
    if (countBadge) {
        const currentCount = parseInt(countBadge.textContent.match(/\d+/)[0]);
        countBadge.textContent = `${currentCount + delta} Schüler`;
    }

    const genderStats = classCard.querySelectorAll('.gender-distribution .gender-stat');
    genderStats.forEach(stat => {
        const text = stat.textContent.trim();
        if (text.startsWith('M ') && gender === 'm') updateStatBadge(stat, delta);
        else if (text.startsWith('W ') && gender === 'w') updateStatBadge(stat, delta);
        else if (text.includes('Förderb.') && hasSpecialNeeds) updateStatBadge(stat, delta);
        else if (text.startsWith('IB ') && isIB) updateStatBadge(stat, delta);
    });
}

/**
 * Update a single stat badge
 */
function updateStatBadge(statElement, delta) {
    const match = statElement.textContent.match(/(\d+)/);
    if (match) {
        const newValue = Math.max(0, parseInt(match[1]) + delta);
        statElement.textContent = statElement.textContent.replace(/\d+/, newValue);
    }
}

/**
 * Show modification indicator
 */
function showModificationIndicator() {
    let indicator = document.getElementById('modification-indicator');
    if (!indicator) {
        indicator = document.createElement('div');
        indicator.id = 'modification-indicator';
        indicator.className = 'modification-indicator';
        indicator.innerHTML = `
            <span></span>
            <button class="btn btn-sm btn-secondary" onclick="location.reload()">Verwerfen</button>
        `;
        const container = document.querySelector('.page-header');
        if (container) container.appendChild(indicator);
    }
    const count = Object.keys(proposalModifications).length;
    indicator.querySelector('span').textContent = `⚠️ ${count} Änderung${count > 1 ? 'en' : ''} im Vorschau-Modus`;
}

/**
 * Escape HTML special characters
 */
function escapeHtml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// --- Legacy: keep old checkConflicts/showConflictDialog/revertMove/acceptConflicts
// for any existing inline calls ---
function checkConflicts(studentId, targetClass) { /* replaced by pre-move flow */ }
function acceptConflicts() { closeMoveModal(); }
function revertMove() { location.reload(); }

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (document.querySelector('.class-card')) {
        initializeDragDrop();
    }
});
