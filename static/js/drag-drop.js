/**
 * Drag & Drop functionality for student movements
 * Allows preview mode changes without saving to database
 */

// State Management
let proposalModifications = {};
let draggedStudent = null;
let originalClass = null;

/**
 * Initialize drag and drop on all student items
 */
function initializeDragDrop() {
    // Make all student items draggable
    const studentItems = document.querySelectorAll('.student-item[draggable="true"]');
    studentItems.forEach(item => {
        item.addEventListener('dragstart', handleDragStart);
        item.addEventListener('dragend', handleDragEnd);
    });

    // Make all class cards droppable
    const classCards = document.querySelectorAll('.class-card');
    classCards.forEach(card => {
        card.addEventListener('dragover', handleDragOver);
        card.addEventListener('drop', handleDrop);
        card.addEventListener('dragleave', handleDragLeave);
    });

    console.log('Drag & Drop initialized');
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

    // Visual feedback
    studentItem.style.opacity = '0.4';
    studentItem.classList.add('dragging');
}

/**
 * Handle drag end event
 */
function handleDragEnd(event) {
    event.currentTarget.style.opacity = '1';
    event.currentTarget.classList.remove('dragging');

    // Remove drag-over class from all class cards
    document.querySelectorAll('.class-card').forEach(card => {
        card.classList.remove('drag-over');
    });
}

/**
 * Handle drag over event
 */
function handleDragOver(event) {
    if (event.preventDefault) {
        event.preventDefault();
    }

    const classCard = event.currentTarget;

    // Don't allow drop on source class
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
    const classCard = event.currentTarget;
    classCard.classList.remove('drag-over');
}

/**
 * Handle drop event
 */
function handleDrop(event) {
    if (event.stopPropagation) {
        event.stopPropagation();
    }

    event.preventDefault();

    const targetClassCard = event.currentTarget;
    const targetClass = targetClassCard.dataset.classId;
    const targetClassName = targetClassCard.dataset.className;

    // Don't allow drop on same class
    if (draggedStudent && targetClass !== draggedStudent.sourceClass) {
        // Move the student element visually
        moveStudentElement(draggedStudent, targetClassCard);

        // Update statistics
        updateClassCounts(draggedStudent.sourceClass, targetClass, draggedStudent.id);

        // Track modification
        proposalModifications[draggedStudent.id] = {
            from: draggedStudent.sourceClass,
            to: targetClass,
            studentName: draggedStudent.name
        };

        // Check for conflicts
        checkConflicts(draggedStudent.id, targetClass);

        // Show modification indicator
        showModificationIndicator();
    }

    targetClassCard.classList.remove('drag-over');
    return false;
}

/**
 * Move student element to target class
 */
function moveStudentElement(student, targetClassCard) {
    const studentList = targetClassCard.querySelector('.student-list');

    if (studentList) {
        // Remove from source
        student.element.remove();

        // Add to target (sorted by name)
        const students = Array.from(studentList.querySelectorAll('.student-item'));
        const studentName = student.name;

        let inserted = false;
        for (let i = 0; i < students.length; i++) {
            const currentName = students[i].dataset.studentName;
            if (studentName.localeCompare(currentName, 'de') < 0) {
                studentList.insertBefore(student.element, students[i]);
                inserted = true;
                break;
            }
        }

        if (!inserted) {
            studentList.appendChild(student.element);
        }

        // Flash animation
        student.element.style.backgroundColor = 'rgba(0, 122, 255, 0.1)';
        setTimeout(() => {
            student.element.style.backgroundColor = '';
        }, 500);
    }
}

/**
 * Update class statistics after move
 */
function updateClassCounts(sourceClassId, targetClassId, studentId) {
    // Get student data
    const studentElement = document.querySelector(`[data-student-id="${studentId}"]`);
    if (!studentElement) return;

    const gender = studentElement.dataset.gender || 'm';
    const hasSpecialNeeds = studentElement.dataset.specialNeeds === 'true';
    const isIB = studentElement.dataset.schulform === 'IB';

    // Update source class
    const sourceCard = document.querySelector(`.class-card[data-class-id="${sourceClassId}"]`);
    if (sourceCard) {
        updateSingleClassCount(sourceCard, gender, hasSpecialNeeds, isIB, -1);
    }

    // Update target class
    const targetCard = document.querySelector(`.class-card[data-class-id="${targetClassId}"]`);
    if (targetCard) {
        updateSingleClassCount(targetCard, gender, hasSpecialNeeds, isIB, 1);
    }
}

/**
 * Update counts for a single class
 */
function updateSingleClassCount(classCard, gender, hasSpecialNeeds, isIB, delta) {
    // Update total count
    const countBadge = classCard.querySelector('.class-count');
    if (countBadge) {
        const currentCount = parseInt(countBadge.textContent.match(/\d+/)[0]);
        countBadge.textContent = `${currentCount + delta} Schüler`;
    }

    // Update gender distribution
    const genderStats = classCard.querySelectorAll('.gender-distribution .gender-stat');
    genderStats.forEach(stat => {
        const text = stat.textContent.trim();
        if (text.startsWith('M ') && gender === 'm') {
            updateStatBadge(stat, delta);
        } else if (text.startsWith('W ') && gender === 'w') {
            updateStatBadge(stat, delta);
        } else if (text.includes('Förderb.') && hasSpecialNeeds) {
            updateStatBadge(stat, delta);
        } else if (text.startsWith('IB ') && isIB) {
            updateStatBadge(stat, delta);
        }
    });
}

/**
 * Update a single stat badge
 */
function updateStatBadge(statElement, delta) {
    const match = statElement.textContent.match(/(\d+)/);
    if (match) {
        const currentValue = parseInt(match[1]);
        const newValue = Math.max(0, currentValue + delta);
        statElement.textContent = statElement.textContent.replace(/\d+/, newValue);
    }
}

/**
 * Check for conflicts via AJAX
 */
function checkConflicts(studentId, targetClass) {
    const csrfToken = document.querySelector('[name="csrf_token"]').value;

    fetch('/check_conflicts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            student_id: studentId,
            target_class: targetClass,
            modifications: proposalModifications
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.conflicts && data.conflicts.length > 0) {
            showConflictDialog(data.conflicts, studentId, targetClass);
        }
    })
    .catch(error => {
        console.error('Error checking conflicts:', error);
    });
}

/**
 * Show conflict dialog
 */
function showConflictDialog(conflicts, studentId, targetClass) {
    // Remove existing dialog
    const existingDialog = document.getElementById('conflict-dialog');
    if (existingDialog) {
        existingDialog.remove();
    }

    // Create dialog
    const dialog = document.createElement('div');
    dialog.id = 'conflict-dialog';
    dialog.className = 'conflict-dialog';

    let conflictHTML = '<h3>⚠️ Konflikte erkannt</h3><ul class="conflict-list">';

    conflicts.forEach(conflict => {
        const severityClass = `conflict-${conflict.severity}`;
        conflictHTML += `<li class="conflict-item ${severityClass}">${conflict.message}</li>`;
    });

    conflictHTML += '</ul>';
    conflictHTML += `
        <div class="conflict-actions">
            <button class="btn btn-secondary" onclick="revertMove('${studentId}')">Rückgängig</button>
            <button class="btn btn-danger" onclick="acceptConflicts()">Akzeptieren</button>
            <button class="btn btn-primary" onclick="showSuggestions('${studentId}', '${targetClass}')">Lösungsvorschläge</button>
        </div>
    `;

    dialog.innerHTML = conflictHTML;

    // Add overlay
    const overlay = document.createElement('div');
    overlay.className = 'conflict-overlay';
    overlay.onclick = () => acceptConflicts();

    document.body.appendChild(overlay);
    document.body.appendChild(dialog);
}

/**
 * Revert a move
 */
function revertMove(studentId) {
    location.reload();
}

/**
 * Accept conflicts and close dialog
 */
function acceptConflicts() {
    const dialog = document.getElementById('conflict-dialog');
    const overlay = document.querySelector('.conflict-overlay');

    if (dialog) dialog.remove();
    if (overlay) overlay.remove();
}

/**
 * Show solution suggestions
 */
function showSuggestions(studentId, targetClass) {
    const csrfToken = document.querySelector('[name="csrf_token"]').value;

    fetch('/suggest_swaps', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            student_id: studentId,
            target_class: targetClass,
            modifications: proposalModifications
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.suggestions && data.suggestions.length > 0) {
            displaySuggestions(data.suggestions);
        } else {
            alert('Keine Lösungsvorschläge verfügbar.');
            acceptConflicts();
        }
    })
    .catch(error => {
        console.error('Error fetching suggestions:', error);
        alert('Fehler beim Laden der Vorschläge.');
    });
}

/**
 * Display solution suggestions
 */
function displaySuggestions(suggestions) {
    const dialog = document.getElementById('conflict-dialog');
    if (!dialog) return;

    let html = '<h3>💡 Lösungsvorschläge</h3>';
    html += '<div class="suggestions-list">';

    suggestions.forEach((suggestion, index) => {
        html += `
            <div class="suggestion-item">
                <div class="suggestion-header">
                    <strong>Vorschlag ${index + 1}</strong>
                    <span class="suggestion-score">Score: ${suggestion.score}/100</span>
                </div>
                <p>${suggestion.description}</p>
                <button class="btn btn-sm btn-primary" onclick="applySuggestion(${index})">Anwenden</button>
            </div>
        `;
    });

    html += '</div>';
    html += '<button class="btn btn-secondary" onclick="acceptConflicts()">Schließen</button>';

    dialog.innerHTML = html;
}

/**
 * Apply a suggestion
 */
function applySuggestion(index) {
    // Placeholder - would implement actual swap logic
    alert('Vorschlag wird angewendet...');
    acceptConflicts();
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
            <span>⚠️ Änderungen im Vorschau-Modus</span>
            <button class="btn btn-sm btn-secondary" onclick="location.reload()">Verwerfen</button>
        `;

        const container = document.querySelector('.page-header');
        if (container) {
            container.appendChild(indicator);
        }
    }

    const count = Object.keys(proposalModifications).length;
    indicator.querySelector('span').textContent = `⚠️ ${count} Änderung${count > 1 ? 'en' : ''} im Vorschau-Modus`;
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on the generate page
    if (document.querySelector('.class-card')) {
        initializeDragDrop();
    }
});
