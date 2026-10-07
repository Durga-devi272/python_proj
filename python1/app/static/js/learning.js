// Learning Interface Interactive Logic

async function markCurrentLessonComplete(lessonId, nextLessonId, courseId) {
  const completeBtn = document.getElementById("mark-complete-btn");
  if (!completeBtn) return;

  const originalContent = completeBtn.innerHTML;
  completeBtn.disabled = true;
  completeBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

  try {
    const response = await fetch(`/api/lessons/${lessonId}/complete`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (!response.ok) {
      throw new Error("Failed to record completion");
    }

    const data = await response.json();

    // Update button state
    completeBtn.classList.remove("btn-primary");
    completeBtn.classList.add("btn-success");
    completeBtn.innerHTML = '<i class="fa-solid fa-check"></i> Completed';
    completeBtn.disabled = true;

    // Update status in sidebar for this lesson
    const statusIcon = document.getElementById(`status-icon-${lessonId}`);
    if (statusIcon) {
      statusIcon.className = "learning-lesson-status status-completed";
      statusIcon.innerHTML = '<i class="fa-solid fa-check"></i>';
    }

    // Update progress bar
    const progressBar = document.getElementById("course-progress-bar");
    const progressText = document.getElementById("course-progress-text");
    if (progressBar && data.course_progress !== undefined) {
      progressBar.style.width = `${data.course_progress}%`;
    }
    if (progressText && data.course_progress !== undefined) {
      progressText.innerText = `${data.course_progress}% Completed`;
    }

    showToast("Lesson completed! Progress saved.", "success");

    // If next lesson exists, prompt or auto-navigate
    if (data.next_lesson_id) {
      setTimeout(() => {
        window.location.href = `/courses/${courseId}/lessons/${data.next_lesson_id}`;
      }, 900);
    } else {
      showToast("🎉 Congratulations! You have finished all lessons in this course.", "success");
    }
  } catch (error) {
    console.error("Error completing lesson:", error);
    completeBtn.disabled = false;
    completeBtn.innerHTML = originalContent;
    showToast("Could not mark lesson complete. Please try again.", "error");
  }
}
